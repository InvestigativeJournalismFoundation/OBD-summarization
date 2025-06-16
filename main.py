import asyncio
from dc_to_s3 import dc_to_s3
from simulate_data import simulate_data


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    exporter = dc_to_s3(project_id=216694, max_documents=300, num_consumers=3)
    asyncio.run(exporter.export_with_queue())
