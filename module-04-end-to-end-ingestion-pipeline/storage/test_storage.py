import sys
from datetime import datetime
from minio_client import MinIOClient
from parquet_writer import ParquetWriter
import logging


logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("parquet-writer-testing")

def main():

    test_events = [
        {
            'event_id' : 'test_002', #test-001,
            'user_id': 1235, #1234,
            'region': 'US',
            'product_id': 'PROD-001',
            'product_name': 'test_product',
            'quantity': 1,
            'amount': 50.50,
            'currency': 'USD',
            'timestamp': int(datetime.now().timestamp() * 1000)

        }        
    ]

    try:

        minio = MinIOClient()
        writer = ParquetWriter(minio)

        logger.info("Writing test batch...")

        success = writer.write_batch(
            events= test_events,
            region='US',
            date_str= datetime.now().strftime('%Y-%m-%d')
        )

        if success:
            logger.info("Test successful!")
            logger.info("Getting statistics...")
            stats = writer.get_statistics()

            logger.info(f"Total files: {stats['total_files']}")
            logger.info(f"By region: {stats['by_region']}")
        else:
            logger.error("Test failed")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")


if __name__ == "__main__":
    main()