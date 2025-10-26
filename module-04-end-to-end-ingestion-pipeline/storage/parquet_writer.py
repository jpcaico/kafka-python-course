import logging
from typing import List, Dict, Any
from datetime import datetime
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq



logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("parquet-writer")

class ParquetWriter:

    def __init__(self, minio_client, bucket_name: str = "bronze-events"):

        self.minio = minio_client
        self.bucket_name = bucket_name
        self.minio.create_bucket(bucket_name)
        logger.info(f"ParquetWriter initialized for bucket: {bucket_name}")


    def write_batch(
            self,
            events: List[Dict[str, Any]],
            region: str,
            date_str: str
    ) -> bool:
        
        "region=US/date=2025-10-24/purchase_timestamp.parquet"

        if not events:
            logger.warning("No events found")
            return False
        
        try:

            df = pd.DataFrame(events)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_name = f"purchases_{timestamp}.parquet"

            object_path = f"region={region}/date={date_str}/{file_name}"

            table = pa.Table.from_pandas(df)

            buffer = io.BytesIO()
            pq.write_table(table, buffer, compression='snappy')

            buffer.seek(0)

            success = self.minio.upload_bytes(
                data = buffer.getvalue(),
                bucket_name = self.bucket_name,
                object_name = object_path
            )

            if success:
                logger.info(f"Wrote {len(events)} events to {object_path}")
                logger.info(f"Size: {len(buffer.getvalue())} bytes")

            return success

        except Exception as e:
            logger.error(f"Failed to upload parquet files: {e}")
            return False
        

    def get_statistics(self) -> Dict[str, Any]:

        stats = {
            'total_files': 0,
            'by_region': {}
        }

        for region in ['US', 'EU', 'ASIA']:
            objects = self.minio.list_objects(
                bucket_name = self.bucket_name,
                prefix = f"region={region}/"
            )

            stats['by_region'][region] = len(objects)
            stats['total_files'] += len(objects)

        return stats


