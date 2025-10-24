import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer
from wrappers.SchemaRegistryWrapper import SchemaRegistryAdmin
from wrappers.ProducerWrapper import KafkaProducer


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

broker = "localhost:9094"
schema_registry_url = "http://localhost:8082"
topic_name = "demo-avro-wrapper"

def load_schema(schema_path: str) -> str:

    try:
        with open(schema_path, 'r') as f:
            logger.info(f"Successfully loaded schema from {schema_path}")
            return f.read()
    except FileNotFoundError:
        logger.error(f"Schema file not found at: {schema_path}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An error occurred while trying to load the schema file: {e}")
        sys.exit(1)


def main():

    parser = argparse.ArgumentParser(description="Kafka avro producer (using schema registry wrapper)")
    parser.add_argument('--schema-file', required=True, help="Path to the Avro (.avsc) file")

    args = parser.parse_args()

    avro_schema_str = load_schema(args.schema_file)
    value_subject_name = f"{topic_name}-value"

    schema_admin = SchemaRegistryAdmin(url=schema_registry_url)

    logger.info(f"Registering schema for subject '{value_subject_name}'")
    schema_admin.register_avro(value_subject_name, avro_schema_str)


    key_serializer = StringSerializer('utf_8')

    value_serializer = AvroSerializer(
        schema_str=avro_schema_str,
        schema_registry_client=schema_admin.client,
        to_dict=lambda obj, ctx:obj
        
    )

    producer = KafkaProducer(
        bootstrap_servers=broker,
        client_id="avro-producer-generic",
        key_serializer=key_serializer,
        value_serializer=value_serializer
    )


    records: list[Dict[str, Any]] = [
    {"user_id": 1, "event": "login" , "timestamp": 1728420000},
    {"user_id": 2, "event": "purchase" , "timestamp": None},
    {"user_id": 3, "event": "logout", "timestamp": 1728420300}
    ]


    logger.info(f"Producing {len(records)} records to topic {topic_name}")

    for record in records:
        
        producer.produce_message(
            topic=topic_name,
            key=str(record["user_id"]),
            value=record
        )

    producer.flush()
    logger.info("All avro messages successfully delivered and flushed.")


if __name__ == "__main__":
    main()



