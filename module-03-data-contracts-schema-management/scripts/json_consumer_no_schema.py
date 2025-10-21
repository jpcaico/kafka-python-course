import json
import logging
from confluent_kafka import Consumer, KafkaError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

topic_name = "demo-topic"
broker = "localhost:9094"
group_id = "json-consumer-group"

c = Consumer({
    'bootstrap.servers': broker,
    'group.id': group_id,
    'auto.offset.reset': 'earliest'
})

c.subscribe([topic_name])

while True:
    msg = c.poll(1.0)
    if msg is None:
        continue

    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        logger.error(f"Consumer error: {msg.error()}")
        continue

    raw_message = msg.value()
    logger.info(f"Received bytes: {raw_message}")

    decoded_message = raw_message.decode("utf-8")

    json_object = json.loads(decoded_message)

    try: 
        user_id = json_object["user_id"]
        logger.info(f"Processed event for user_id: {user_id}")
    except KeyError:
        logger.error(f"Key 'user_id' not found in the json message.")

    print(json_object)
