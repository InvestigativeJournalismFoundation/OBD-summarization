import asyncio
from dc_to_s3 import dc_to_s3
from sum_from_S3 import DocumentStatsCollector
from sum_stats import DocumentStatsAnalyzer

# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # exporter = dc_to_s3(project_id=216694, max_documents=30000, num_consumers=3)
    # asyncio.run(exporter.export_with_queue())

    # collector = DocumentStatsCollector(
    #     bucket_name="obd-sum-stats",
    #     prefix="",
    #     workers=8
    # )
    # asyncio.run(collector.process_documents_async())

    analyzer = DocumentStatsAnalyzer(
            doc_stats_path="data/document_stats.csv",
            page_tokens_path="data/page_token_counts.csv"
        )
    analyzer.load_data()
    analyzer.show_summary()
    analyzer.plot_all()