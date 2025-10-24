import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from wrappers.SchemaRegistryWrapper import SchemaRegistryAdmin
from wrappers.ConsumerWrapper import KafkaConsumer


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

broker = "localhost:9094"
schema_registry_url = "http://localhost:8082"
topic_name = "demo-avro-wrapper"
consumer_group_id = "avro-generic-consumers"


def main():
    logger.info("Starting avro consumer")

    schema_admin = SchemaRegistryAdmin(url=schema_registry_url)

    key_deserializer = StringDeserializer('utf_8')

    value_deserializer = AvroDeserializer(schema_admin.client)

    consumer = KafkaConsumer(
        bootstrap_servers=broker,
        group_id=consumer_group_id,
        auto_offset_reset='earliest',
        key_deserializer=key_deserializer,
        value_deserializer=value_deserializer
    )

    consumer.subscribe([topic_name])
    consumer.consume_messages()

if __name__ == "__main__":
    main()


