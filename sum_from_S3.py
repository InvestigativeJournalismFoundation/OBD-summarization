import os
import json
import csv
import asyncio
from asyncio import Semaphore, create_task, as_completed
import aioboto3
import pandas as pd
import spacy
from tqdm.asyncio import tqdm as async_tqdm
from concurrent.futures import ProcessPoolExecutor
from statistics import mean
from pathlib import Path
from dotenv import load_dotenv


def process_document_bytes(doc_bytes: bytes):
    nlp = spacy.load("en_core_web_sm")
    doc = json.loads(doc_bytes)

    metadata = doc.get("metadata", {})
    meta_data = metadata.get("data", {})

    doc_id = str(doc.get("doc_id", ""))
    pages = doc.get("text_json", {}).get("pages", [])
    sorted_pages = sorted(pages, key=lambda x: x.get("page", 0))
    texts = [page.get("contents", "") for page in sorted_pages]
    token_counts = [len(nlp(page)) for page in texts]

    doc_stats = {
        "doc_id": doc_id,
        "title": metadata.get("title", ""),
        "organization": meta_data.get("organization", [""])[0],
        "request_number": meta_data.get("request_number", [""])[0],
        "description": metadata.get("description", ""),
        "created_at": metadata.get("created_at", ""),
        "page_count": metadata.get("page_count", len(pages)),
        "file_size": int(meta_data.get("file_size", [0])[0]),
        "token_total": sum(token_counts),
        "token_avg_per_page": mean(token_counts) if token_counts else 0,
        "token_min": min(token_counts) if token_counts else 0,
        "token_max": max(token_counts) if token_counts else 0,
        "token_std_dev": pd.Series(token_counts).std() if len(token_counts) > 1 else 0,
    }

    page_stats = [
        {"doc_id": doc_id, "page_number": i, "tokens_per_page": count}
        for i, count in enumerate(token_counts)
    ]

    return doc_stats, page_stats


class DocumentStatsCollector:
    def __init__(self, bucket_name: str, prefix: str = "", workers: int = 4):
        load_dotenv()
        self._S3_BUCKET = bucket_name
        self.prefix = prefix
        self.workers = workers
        self.doc_csv_path = Path("document_stats.csv")
        self.page_csv_path = Path("page_token_counts.csv")
        self.already_summed_docs = set()
        self._load_existing_doc_ids()

    def _load_existing_doc_ids(self):
        if self.doc_csv_path.exists():
            with open(self.doc_csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.already_summed_docs.add(row["doc_id"])
            print(f"Resuming from {len(self.already_summed_docs)} documents already processed.")

    def list_s3_keys(self):
        import boto3
        client = boto3.client(
            "s3",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ["AWS_REGION"]
        )
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._S3_BUCKET, Prefix=self.prefix):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".json"):
                    yield obj["Key"]

    async def fetch_document(self, s3, key, semaphore):
        async with semaphore:
            try:
                print(f"Fetching: {key}")
                response = await s3.get_object(Bucket=self._S3_BUCKET, Key=key)
                body = await response["Body"].read()
                print(f"Fetched: {key}")
                doc = json.loads(body)
                doc_id = doc.get("doc_id")
                if doc_id in self.already_summed_docs:
                    return None, None
                return doc_id, body
            except Exception as e:
                print(f"Failed to fetch {key}: {e}")
                return None, None

    async def stream_docs(self, semaphore_limit=10):
        session = aioboto3.Session()
        semaphore = asyncio.Semaphore(semaphore_limit)

        async with session.client(
                "s3",
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                region_name=os.environ["AWS_REGION"]
        ) as s3:
            for key in self.list_s3_keys():
                if key.split(".")[0] in self.already_summed_docs:
                    continue
                async with semaphore:
                    try:
                        response = await s3.get_object(Bucket=self._S3_BUCKET, Key=key)
                        body = await response["Body"].read()
                        doc = json.loads(body)
                        doc_id = doc.get("doc_id")
                        if not doc_id:
                            continue
                        yield doc_id, body
                    except Exception as e:
                        print(f"Failed to fetch {key}: {e}")

    async def process_documents_async(self):

        # Get a streaming async generator of doc_id + body
        loop = asyncio.get_running_loop()
        processed = 0

        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            async for doc_id, body in async_tqdm(self.stream_docs(), desc="Processing docs"):
                try:
                    future = loop.run_in_executor(pool, process_document_bytes, body)
                    doc_stats, page_stats = await future

                    with open(self.doc_csv_path, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(list(doc_stats.values()))

                    with open(self.page_csv_path, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerows([
                            [r["doc_id"], r["page_number"], r["tokens_per_page"]] for r in page_stats
                        ])
                    self.already_summed_docs.add(doc_id)
                    print(f"Wrote doc: {doc_id}")
                    processed += 1
                except Exception as e:
                    print(f"Failed to process {doc_id}: {e}")

        # Change the column names at the end
        try:
            doc_cols = [
                "doc_id", "title", "organization", "request_number", "description",
                "created_at", "page_count", "file_size", "token_total",
                "token_avg_per_page", "token_min", "token_max", "token_std_dev"
            ]
            page_cols = ["doc_id", "page_number", "tokens_per_page"]

            doc_df = pd.read_csv(self.doc_csv_path, header=None)
            doc_df.columns = doc_cols
            doc_df.to_csv(self.doc_csv_path, index=False)

            page_df = pd.read_csv(self.page_csv_path, header=None)
            page_df.columns = page_cols
            page_df.to_csv(self.page_csv_path, index=False)

            print(f"Added headers to CSVs after writing {processed} documents.")
        except Exception as e:
            print(f"Failed to add CSV headers: {e}")
