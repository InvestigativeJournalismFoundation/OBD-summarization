import os
import boto3
import json
import pandas as pd
from statistics import mean
import spacy
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor, as_completed


def process_document_bytes(doc_bytes: bytes, spacy_model: str = "en_core_web_sm"):
    nlp = spacy.load(spacy_model)
    doc = json.loads(doc_bytes)

    metadata = doc.get("metadata", {})
    meta_data = metadata.get("data", {})
    doc_id = str(doc.get("doc_id", ""))
    pages = doc.get("text_json", {}).get("pages", [])
    sorted_pages = sorted(pages, key=lambda x: x.get("page", 0))
    texts = [page.get("contents", "") for page in sorted_pages]
    token_counts = [len(nlp(page)) for page in texts]

    # Document-level summary
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

    # Page-level stats
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
        self._s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ["AWS_REGION"],
        )
        self.workers = workers
        self.records = []
        self.page_records = []

    def list_s3_keys(self):
        paginator = self._s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._S3_BUCKET, Prefix=self.prefix):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".json"):
                    yield obj["Key"]

    def process_documents(self, limit: int = None):
        print("Fetching keys ...")
        keys = list(self.list_s3_keys())
        if limit:
            keys = keys[:limit]

        print(f"Processing {len(keys)} documents with {self.workers} workers ...")

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures = []
            for key in keys:
                try:
                    obj = self._s3_client.get_object(Bucket=self._S3_BUCKET, Key=key)
                    doc_bytes = obj["Body"].read()
                    futures.append(executor.submit(process_document_bytes, doc_bytes))
                except Exception as e:
                    print(f"Failed to fetch {key}: {e}")

            for future in tqdm(as_completed(futures), total=len(futures)):
                try:
                    doc_stats, page_stats = future.result()
                    self.records.append(doc_stats)
                    self.page_records.extend(page_stats)
                except Exception as e:
                    print(f"Processing error: {e}")

    def save_page_csv(self, path: str):
        df = pd.DataFrame(self.page_records)
        df.to_csv(path, index=False)
        print(f"Saved {len(df)} page-level records to {path}")

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.records)

    def save_csv(self, path: str):
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        print(f"Saved {len(df)} records to {path}")

