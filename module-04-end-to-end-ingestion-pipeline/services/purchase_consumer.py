import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import time
import yaml

from confluent_kafka.serialization import StringDeserializer
from confluent_kafka.schema_registry.avro import AvroDeserializer

project_root = Path(__file__).parent.parent.parent
project_rootw = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_rootw))

from wrappers.ConsumerWrapper import KafkaConsumer
from wrappers.SchemaRegistryWrapper import SchemaRegistryAdmin
from storage.minio_client import MinIOClient
from storage.parquet_writer import ParquetWriter

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("purchase-consumer")

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
    

def flush_batches(event_batches: Dict[str, List], parquet_writer, stats: Dict, region: str = None):

    regions_to_flush = [region] if region else list(event_batches.keys())
    date_str = datetime.now().strftime('%Y-%m-%d')

    for reg in regions_to_flush:
        events = event_batches.get(reg, [])

        if not events:
            continue

        success = parquet_writer.write_batch(
            events=events,
            region=reg,
            date_str=date_str
        )

        if success:
            batch_count = len(events)
            stats['total_written'] += batch_count
            stats['batches_written'] += 1

            logger.info(f"Flushed {batch_count} {reg} events")
            logger.info(f"Total written : {stats['total_written']}")

            event_batches[reg] = []



def main():

    config = load_config()

    BATCH_SIZE = 50 
    BATCH_TIMEOUT_SECONDS = 30

    logger.info(f"Initializing Components...")

    schema_admin = SchemaRegistryAdmin(url=config['kafka']['schema_registry_url'])

    consumer = KafkaConsumer(
        bootstrap_servers=','.join(config['kafka']['bootstrap_servers']),
        group_id='purchase-ingestion-consumers',
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        key_deserializer=StringDeserializer('utf_8'),
        value_deserializer=AvroDeserializer(schema_admin.client)
    )

    topic_name = config['kafka']['topics']['purchases']
    consumer.subscribe([topic_name])

    parquet_writer = ParquetWriter(MinIOClient())

    event_batches: Dict[str,List] = defaultdict(list)
    last_flush_time = time.time()
    stats = {
        'total_consumed': 0,
        'total_written': 0,
        'batches_written': 0,
        'by_region': defaultdict(int)
    }


    def process_event(key, value, msg):

        nonlocal last_flush_time

        if (time.time() - last_flush_time) >= BATCH_TIMEOUT_SECONDS:
            logger.info("Batch timeout reached, flushing all batches")
            flush_batches(event_batches, parquet_writer, stats)
            last_flush_time = time.time()

        if value and value.get('region'):
            region = value['region']


            event_batches[region].append(value)
            stats['total_consumed'] +=1
            stats['by_region'][region] +=1

            if len(event_batches[region]) >= BATCH_SIZE:
                flush_batches(event_batches, parquet_writer, stats, region=region)

            if stats['total_consumed'] % 50 == 0:
                pending = sum(len(b) for b in event_batches.values())
                logger.info(f"Progress: consumed={stats['total_consumed']}")
                logger.info(f"Written={stats['total_written']}")
                logger.info(f"Pending={pending}")

        consumer.consumer.commit(message=msg, asynchronous=True)

    logger.info("Starting the consumer loop, press Ctrl+C to stop")
    logger.info(f"Topic: {topic_name} | Batch size: {BATCH_SIZE} | Timeout: {BATCH_TIMEOUT_SECONDS}s" )

    try:
        consumer.consume_messages(process_callback=process_event)
    finally:
        logger.info(f"Flushing remaining batches...")
        flush_batches(event_batches, parquet_writer, stats)

        logger.info(f"Total Consumed: {stats['total_consumed']}")
        logger.info(f"Total written: {stats['total_written']}")
        logger.info(f"Batches written: {stats['batches_written']}")
        logger.info(f"By region: {dict(stats['by_region'])}")

        storage_stats = parquet_writer.get_statistics()
        logger.info(f"Total files: {storage_stats['total_files']}")
        logger.info(f"By region: {storage_stats['by_region']}")

        logger.info(f"Consumer closed.")

if __name__ == "__main__":
    main()