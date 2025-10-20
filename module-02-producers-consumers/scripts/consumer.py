import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wrappers.ConsumerWrapper import KafkaConsumer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

topic_name = ["demo-topic"]
broker = "localhost:9094"
consumer_group = "demo-consumer"


consumer = KafkaConsumer(
    bootstrap_servers=broker,
    group_id=consumer_group,
    auto_offset_reset="earliest",
    enable_auto_commit=True
)

consumer.subscribe(topic_name)
logger.info(f"Successfully subscribed to topics: {topic_name}")
consumer.consume_messages()