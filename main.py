import asyncio
from dc_to_s3 import dc_to_s3
from sum_from_S3 import DocumentStatsCollector

# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # exporter = dc_to_s3(project_id=216694, max_documents=30000, num_consumers=3)
    # asyncio.run(exporter.export_with_queue())

    collector = DocumentStatsCollector(
        bucket_name="obd-sum-stats",
        prefix="",
        workers=4
    )
    collector.process_documents()
    collector.save_csv("document_stats.csv")
    collector.save_page_csv("page_token_counts.csv")
