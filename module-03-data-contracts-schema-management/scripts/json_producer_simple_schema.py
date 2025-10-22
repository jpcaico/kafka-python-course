import logging
import argparse
import sys

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import SerializationContext, MessageField, StringSerializer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


broker = "localhost:9094"
schema_registry_url = "http://localhost:8082"
topic_name = "demo-json"

def load_schema(schema_path: str) -> str:

    try:
        with open(schema_path, 'r') as f:
            log.info(f"Successfully loaded schema from {schema_path}")
            return f.read()
    except FileNotFoundError:
        log.error(f"Schema file not found at: {schema_path}")
        sys.exit(1)
    except Exception as e:
        log.exception(f"An error occurred while trying to load the schema file: {e}")
        sys.exit(1)


def delivery_call(err, msg):
    if err is not None:
        log.error(f"Delivered failed for record with the key {msg.key()}: {err}")
        return
    log.info(f"Delivered record with key {msg.key().decode('utf-8')}")
    log.info(f"To {msg.topic()} and Partition {msg.partition()} @ offset {msg.offset()}")


# python3 json_producer_simple_schema.py --schema-file ./schemas/users_event_schema.json
parser = argparse.ArgumentParser(description="Kafka JSON Producer with External Schema")
parser.add_argument('--schema-file', required=True, help="Path to the JSON schema file")
args = parser.parse_args()

json_schema_str = load_schema(args.schema_file)


producer = Producer({
    "bootstrap.servers": broker,
    "client.id": "json-producer-file",
    "acks": "all"
})


key_serializer = StringSerializer("utf_8")

sr_client = SchemaRegistryClient({"url": schema_registry_url})

json_serializer = JSONSerializer(

    json_schema_str,
    sr_client,
    to_dict=lambda obj, ctx: obj
)



records = [

{"user_id": 1, "event": "login", "timestamp": 1728420000},
{"user_id": 2, "event": "purchase"},
{"user_id": 3, "event": "logout", "timestamp": 1728420300},

]

log.info(f"Producing {len(records)} records to topic: {topic_name}")


for rec in records:
    try:
        producer.produce(
            topic=topic_name,
            key=key_serializer(str(rec["user_id"])),
            value= json_serializer(rec, SerializationContext(topic_name, MessageField.VALUE)),
            on_delivery = delivery_call

            )

        
    except Exception as e:
        log.exception(f"Failed to produce record {rec}: {e}")

producer.flush(10)

log.info("All messages flushed from producer buffer.")