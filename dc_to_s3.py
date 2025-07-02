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
        self._uname = os.environ["DOCUMENTCLOUD_USERNAME"]
        self._pw = os.environ["DOCUMENTCLOUD_PASSWORD"]
        self._token = None
        self._token_expiry = datetime.fromtimestamp(0)
        self._session = ClientSession()

    async def _get_new_token(self) -> str:
        formdata = {"username": self._uname, "password": self._pw}
        res = await self._session.post(
            "https://accounts.muckrock.com/api/token/",
            data=formdata,
            allow_redirects=True,
        )
        if not res.ok:
            res.raise_for_status()
        return json.loads(await res.text())["access"]

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
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ["AWS_REGION"],
        )
        self._DC_URL = "https://api.www.documentcloud.org/api/projects/"
        self._PROJECT_ID = project_id
        self._max_documents = max_documents
        self._num_consumers = num_consumers

    # Fetch a batch of documents from DC
    async def fetch_document_batches(self, session: ClientSession, project_id: int, batch_size: int = 100):
        dctk = DCToken()
        token = await dctk.token()

        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self._DC_URL}{project_id}/documents/?per_page={batch_size}"
        total_fetched = 0

        while url and total_fetched < self._max_documents:
            async with session.get(url, headers=headers) as res:
                if res.status == 403:
                    await asyncio.sleep(5)
                    continue
                if res.status == 429:
                    msg = await res.text()
                    print("429 Received:", msg)
                res.raise_for_status()
                data = await res.json()
                results = data.get("results", [])
                total_fetched += len(results)
                yield results
                url = data.get("next")
                await asyncio.sleep(1)

    # Pack a document onj
    async def get_document_obj(self, session: ClientSession, doc_id: int) -> dict:
        dctk = DCToken()
        token = await dctk.token()
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

    # Upload a doc to S3 and log it
    async def process_document(self, session: ClientSession, doc_id: int, empty_path: str):
        try:
            doc_bundle = await self.get_document_obj(session, doc_id)
            if not doc_bundle["text_json"]:
                with open(empty_path, "a") as f:
                    f.write(f"{doc_id}\n")
            await self.upload_document_to_s3(doc_bundle, cache_path="uploaded_ids_cache.txt")
        except Exception as e:
            print(f"Error with {doc_id}: {e}")

    # Uploading helper
    async def upload_document_to_s3(self, doc_bundle: dict, cache_path):
        doc_id = doc_bundle["doc_id"]
        buffer = BytesIO(json.dumps(doc_bundle, indent=2).encode("utf-8"))
        self._s3_client.upload_fileobj(buffer, self._S3_BUCKET, f"{doc_id}.json")
        print(f"Uploaded {doc_id}")

        # Append to cache
        with open(cache_path, "a") as f:
            f.write(f"{doc_id}\n")

    async def consumer(self, queue, session, empty_path, total_pending, completed_lock, completed_count_ref):
        while True:
            doc_id = await queue.get()
            if doc_id is None:
                queue.task_done()
                break
            try:
                await self.process_document(session, int(doc_id), empty_path)
                async with completed_lock:
                    completed_count_ref[0] += 1
                    print(f"Progress: {completed_count_ref[0]}/{len(total_pending)} done")
            finally:
                queue.task_done()

    # Get the list of docs in S3
    async def list_uploaded_ids_s3(self, cache_path="uploaded_ids_cache.txt") -> set:
        if os.path.exists(cache_path):
            print(f"Using cached uploaded IDs from {cache_path}")
            with open(cache_path, "r") as f:
                return set(line.strip() for line in f)

        print("Fetching uploaded IDs from S3...")
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

        # Save to cache
        with open(cache_path, "w") as f:
            for doc_id in uploaded_ids:
                f.write(f"{doc_id}\n")

        print(f"Cached {len(uploaded_ids)} uploaded document IDs")
        return uploaded_ids

    async def load_or_fetch_dc_doc_ids(self, session: ClientSession, cache_path="dc_document_ids_cache.txt") -> set:
        if os.path.exists(cache_path):
            print(f"Using cached DC document IDs from {cache_path}")
            with open(cache_path, "r") as f:
                return set(line.strip() for line in f)

        print("Fetching document IDs from DocumentCloud API...")

        url = f"{self._DC_URL}{self._PROJECT_ID}/documents/?per_page=100"
        doc_ids = set()

        with open(cache_path, "w") as f:
            while url:
                dctk = DCToken()
                token = await dctk.token()
                headers = {"Authorization": f"Bearer {token}"}

                async with session.get(url, headers=headers) as res:
                    if res.status == 403:
                        print("Got 403")
                        await asyncio.sleep(5)
                        continue
                    if res.status == 429:
                        print("Rate limited while fetching DC document list.")
                        await asyncio.sleep(10)
                        continue
                    res.raise_for_status()
                    data = await res.json()
                    results = data.get("results", [])

                    new_ids = [str(entry["document"]) for entry in results]
                    for doc_id in new_ids:
                        if doc_id not in doc_ids:
                            f.write(f"{doc_id}\n")
                            doc_ids.add(doc_id)

                    print(f"Fetched {len(new_ids)} more, total so far: {len(doc_ids)}")

                    url = data.get("next")
                    if not url:
                        print("Reached end of document list.")
                        break

                    await asyncio.sleep(1)

        print(f"Wrote {len(doc_ids)} total IDs to {cache_path}")
        return doc_ids

    # main() will call this
    async def export_with_queue(self):
        empty_path = "empty_docs_all.txt" # log documents with no texts
        queue = asyncio.Queue(maxsize=100)

        async with ClientSession() as session:

            print("Checking S3 bucket")
            paginator = self._s3_client.get_paginator("list_objects_v2")
            current_bucket = set()

            try:
                for page in paginator.paginate(Bucket=self._S3_BUCKET):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        if key.endswith(".json"):
                            doc_id = key.replace(".json", "")
                            current_bucket.add(doc_id)
            except Exception as e:
                print(f"Failed to list objects in S3: {e}")

            uploaded_ids = await self.list_uploaded_ids_s3()
            print(f"{len(current_bucket)} documents are already in the S3 bucket.")

            completed_count_ref = [0]
            completed_lock = asyncio.Lock()

            dc_doc_ids = await self.load_or_fetch_dc_doc_ids(session)
            pending_ids = dc_doc_ids - uploaded_ids

            print(f"Found {len(pending_ids)} pending documents")

            consumer_tasks = [
                asyncio.create_task(
                    self.consumer(queue, session, empty_path, pending_ids, completed_lock, completed_count_ref)
                )
                for _ in range(self._num_consumers)
            ]

            total_added = 0
            newly_added = 0
            for doc_id in pending_ids:
                await queue.put(doc_id)
                total_added += 1
                newly_added += 1
                if total_added >= self._max_documents:
                    break

            print(f"Enqueued {newly_added} new documents")

            await queue.join()
            for _ in range(self._num_consumers):
                await queue.put(None)
            await asyncio.gather(*consumer_tasks)
