import asyncio
import json
import os
from datetime import datetime, timedelta
from io import BytesIO
import boto3
from aiohttp import ClientSession
from dotenv import load_dotenv


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class DCToken(metaclass=Singleton):
    def __init__(self) -> None:
        load_dotenv()
        self._uname = os.getenv("DOCUMENTCLOUD_USERNAME")
        self._pw = os.getenv("DOCUMENTCLOUD_PASSWORD")
        self._token = None
        self._token_expiry = datetime.fromtimestamp(0)
        self._session = ClientSession()

    async def _get_new_token(self) -> str:
        formdata = {"username": self._uname, "password": self._pw}
        async with self._session.post("https://accounts.muckrock.com/api/token/", data=formdata) as res:
            res.raise_for_status()
            return (await res.json())["access"]

    async def token(self):
        now = datetime.now()
        if self._token_expiry < now:
            self._token = await self._get_new_token()
            self._token_expiry = now + timedelta(minutes=4, seconds=50)
        return self._token


class dc_to_s3:
    def __init__(self, project_id, max_documents, num_consumers) -> None:
        load_dotenv()
        self._S3_BUCKET = "obd-sum-stats"
        self._s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        self._DC_URL = "https://api.www.documentcloud.org/api/projects/"
        self._PROJECT_ID = project_id
        self._max_documents = max_documents
        self._num_consumers = num_consumers

    # Fetch a batch of documents from DC
    async def fetch_document_batches(self, session: ClientSession, project_id: int, batch_size: int = 100):
        token = await DCToken().token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self._DC_URL}{project_id}/documents/?per_page={batch_size}"
        total_fetched = 0

        while url and total_fetched < self._max_documents:
            async with session.get(url, headers=headers) as res:
                if res.status == 403:
                    await asyncio.sleep(5)
                    continue
                res.raise_for_status()
                data = await res.json()
                results = data.get("results", [])
                total_fetched += len(results)
                yield results
                url = data.get("next")
                await asyncio.sleep(0.1)

    # Pack a document onj
    async def get_document_obj(self, session: ClientSession, doc_id: int) -> dict:
        token = await DCToken().token()
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(f"https://api.www.documentcloud.org/api/documents/{doc_id}/", headers=headers) as meta_res:
            meta_res.raise_for_status()
            metadata = await meta_res.json()
        asset_url = metadata.get("asset_url")
        slug = metadata.get("slug")
        if not asset_url:
            raise ValueError(f"No asset_url found for {doc_id}")
        static_text_url = f"{asset_url}documents/{doc_id}/{slug}.txt.json"
        async with session.get(static_text_url) as text_res:
            if text_res.status == 404:
                print(f"No text JSON found for {doc_id}")
                return {"doc_id": doc_id, "metadata": metadata, "text_json": {}}
            text_res.raise_for_status()
            text_json = await text_res.json()
        return {"doc_id": doc_id, "metadata": metadata, "text_json": text_json}

    # Write local log of docs
    def save_processed_id(self, doc_id: int, path: str):
        with open(path, "a") as f:
            f.write(f"{doc_id}\n")

    # Read local log of docs
    def load_processed_ids(self, path: str) -> set:
        if not os.path.exists(path): return set()
        with open(path, "r") as f:
            return set(line.strip() for line in f)

    # Upload a doc to S3 and log it
    async def process_document(self, session: ClientSession, doc_id: int, processed_path: str, empty_path: str):
        try:
            doc_bundle = await self.get_document_obj(session, doc_id)
            if not doc_bundle["text_json"]:
                with open(empty_path, "a") as f:
                    f.write(f"{doc_id}\n")
            await self.upload_document_to_s3(doc_bundle)
            self.save_processed_id(doc_id, processed_path)
        except Exception as e:
            print(f"Error with {doc_id}: {e}")

    # Uploading helper
    async def upload_document_to_s3(self, doc_bundle: dict):
        doc_id = doc_bundle["doc_id"]
        buffer = BytesIO(json.dumps(doc_bundle, indent=2).encode("utf-8"))
        self._s3_client.upload_fileobj(buffer, self._S3_BUCKET, f"{doc_id}.json")
        print(f"Uploaded {doc_id}")

    async def consumer(self, queue, session, processed_path, empty_path, pending, completed_lock, completed_count_ref):
        while True:
            doc_id = await queue.get()
            if doc_id is None:
                queue.task_done()
                break
            try:
                await self.process_document(session, int(doc_id), processed_path, empty_path)
                async with completed_lock:
                    completed_count_ref[0] += 1
                    print(f"Progress: {completed_count_ref[0]}/{len(pending)} done")
            finally:
                queue.task_done()

    # Get the list of docs in S3
    async def list_uploaded_ids_s3(self) -> set:
        paginator = self._s3_client.get_paginator("list_objects_v2")
        uploaded_ids = set()
        try:
            for page in paginator.paginate(Bucket=self._S3_BUCKET):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith(".json"):
                        doc_id = key.replace(".json", "")
                        uploaded_ids.add(doc_id)
        except Exception as e:
            print(f"Failed to list objects in S3: {e}")
        return uploaded_ids

    # main() will call this
    async def export_with_queue(self):
        processed_path = "processed_docs_all.txt" # log processed docs
        empty_path = "empty_docs_all.txt" # log documents with no texts
        queue = asyncio.Queue(maxsize=100)

        async with ClientSession() as session:
            processed_ids = self.load_processed_ids(processed_path)
            uploaded_ids = await self.list_uploaded_ids_s3()
            all_uploaded = processed_ids.intersection(uploaded_ids) # docs are marked as processed if they are both logged by local and s3

            completed_count_ref = [0]
            completed_lock = asyncio.Lock()

            consumer_tasks = [
                asyncio.create_task(
                    self.consumer(queue, session, processed_path, empty_path, all_uploaded, completed_lock, completed_count_ref)
                )
                for _ in range(self._num_consumers)
            ]

            total_added = 0
            async for batch in self.fetch_document_batches(session, self._PROJECT_ID):
                pending_batch = [entry["document"] for entry in batch if str(entry["document"]) not in all_uploaded]
                for doc_id in pending_batch:
                    await queue.put(doc_id)
                    total_added += 1
                    if total_added >= self._max_documents:
                        break
                if total_added >= self._max_documents:
                    break

            print(f"Enqueued {total_added} new documents")

            await queue.join()
            for _ in range(self._num_consumers):
                await queue.put(None)
            await asyncio.gather(*consumer_tasks)
