import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wrappers.ProducerWrapper import KafkaProducer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

topic_name = "demo-topic"
broker = "localhost:9094"

producer = KafkaProducer(

    bootstrap_servers=broker,
    acks="all",
    enable_idempotence=True,
    linger_ms=5,
    batch_size=64_000,
    compression_type="snappy",
    retries=1_000_000

)


# try:
#     print(f"Interactive mode. Type messages to send to kafka.")
#     print("Type 'exit' or 'quit' to stop\n")

#     while True:
#         line = input("kafka> ").strip()
#         if not line:
#             continue
#         if line.lower() in ("exit", "quit"):
#             break

#         producer.produce_message(topic=topic_name, value=line)
# except (KeyboardInterrupt, EOFError):
#     print()

for i in range(10):
    msg = f"Hello my friend! This is message: #{i}"
    producer.produce_message(topic=topic_name, value=msg)
    logger.info(f"Sent {msg}")
    time.sleep(0.5)

producer.flush()

logger.info("Kaka producer was closed")

