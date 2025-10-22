import logging
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import StringDeserializer, SerializationContext, MessageField

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


broker = "localhost:9094"
schema_registry_url = "http://localhost:8082"
topic_name = "demo-json"
group_id = "json-consumer-group"

consumer = Consumer({
    "bootstrap.servers": broker,
    "group.id": group_id,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True
})

sr_client = SchemaRegistryClient({"url": schema_registry_url})

key_deserializer = StringDeserializer("utf_8")

json_deserializer = JSONDeserializer(
    schema_str = None,
    schema_registry_client = sr_client,
    from_dict= lambda obj, ctx:obj
)

consumer.subscribe([topic_name])
log.info(f"Consuming from topic {topic_name}")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            log.error(f"Error: {msg.error()}")
            continue

        key = key_deserializer(msg.key() if msg.key() else None)

        ctx = SerializationContext(msg.topic(), MessageField.VALUE)
        value = json_deserializer(msg.value(), ctx)

        log.info(f"Key: {key}, Value: {value}")

except KeyboardInterrupt:
    log.info("Stopped by the user")
finally:
    consumer.close()