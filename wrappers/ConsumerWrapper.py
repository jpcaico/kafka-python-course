import logging
from typing import List, Any, Optional
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.serialization import SerializationContext, MessageField

logging.basicConfig(
    level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class KafkaConsumer:

    def __init__(
            
        self,
        bootstrap_servers: str,
        group_id: str,
        *,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True, 

        key_deserializer: Optional[Any] = None,
        value_deserializer: Optional[Any] = None


    ):
        
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": enable_auto_commit
        }

        self.consumer = Consumer(self.config)
        self.running = False 

        self.key_deserializer = key_deserializer
        self.value_deserializer = value_deserializer

        logger.info(f"Consumer initialized: group={group_id}, brokers={bootstrap_servers}")


    def subscribe(self, topics: List[str]) -> None:
        if not topics:
            raise ValueError("Please provide at least one topic to subscribe to")
        
        self.consumer.subscribe(topics)
        logger.info(f"Subscribed to topics: {topics}")


    def process_message(self, msg, process_callback=None) -> None:
        topic = msg.topic()
        partition = msg.partition()
        offset = msg.offset()
        key = None
        value = None

        #key
        try:
            if msg.key() is not None:
                if self.key_deserializer:
                    key = self.key_deserializer(msg.key())
                else:
                    key = msg.key().decode("utf-8")
        except UnicodeDecodeError:
            key = msg.key()

        #value

        try:
            if msg.value() is not None:
                if self.value_deserializer:
                    value = self.value_deserializer(
                        msg.value(),
                        SerializationContext(topic, MessageField.VALUE)

                    )
                else:
                    value = msg.value().decode("utf-8")
        except UnicodeDecodeError:
            value = msg.value()


        if process_callback:
            process_callback(key, value, msg)
        else:
            logger.info(f"Message received: topic={topic}, partition={partition}, offset={offset}, key={key}, value={value}")


    def consume_messages(self, process_callback=None) -> None:
        self.running = True
        logger.info("Starting consumer loop (Press Ctrl+C to stop)")

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue
            
                self.process_message(msg, process_callback)
        except KeyboardInterrupt:
            logger.info(f"Interrupted by user")

        finally:
            self.close()


    def close(self) -> None:
        logger.info("Closing the consumer")
        self.consumer.close()
        logger.info("Consumer closed")

    def stop(self) -> None:
        self.running = False