from confluent_kafka import Producer, KafkaException
import logging
from typing import Any, Union, List, Optional
from confluent_kafka.serialization import SerializationContext, MessageField

logging.basicConfig(level=logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class KafkaProducer:

    def __init__(
    self,
    bootstrap_servers: Union[str, List[str]],
    *,
    client_id: str = "basic-producer",
    acks: str = 'all', 
    enable_idempotence: bool = True, 
    linger_ms: int = 5, 
    batch_size: int = 64_000,
    compression_type: str = "snappy",
    retries: int = 1_000_000,
    key_serializer: Optional[Any] = None,
    value_serializer: Optional[Any] = None


    ):
        
        if isinstance(bootstrap_servers, list):
            bootstrap_servers = ",".join(bootstrap_servers)

        
        self.config = {

        "bootstrap.servers": bootstrap_servers,
        "client.id": client_id,

        "acks": acks, 
        "enable.idempotence": enable_idempotence,
        "retries": retries,

        "linger.ms": linger_ms,
        "batch.size": batch_size,

        "compression.type": compression_type


        }

        self.producer = Producer(self.config)

        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

        logger.info(f"Kafka producer initialized with brokers: {bootstrap_servers}")


    
    def delivery_report(self, err, msg):
        if err:
            logger.error(f"Delivery failed : {err} ")
        else:
            logger.info(
                f"Record succesfully delivered to topic= {msg.topic()}\n"
                f"Partition={msg.partition()} offset={msg.offset()}"

            )

    
    def produce_message(self, topic: str, value: Any, key: Optional[Any]=None):

        record_key = key
        record_value = value


        try:
            if self.key_serializer and key is not None:
                record_key = self.key_serializer(key)
            
            if self.value_serializer and value is not None:
                record_value = self.value_serializer(
                    value,
                    SerializationContext(topic, MessageField.VALUE)
                )

            
            self.producer.produce(
                topic=topic,
                key=record_key,
                value=record_value,
                callback= self.delivery_report
            )

            self.producer.poll(0)
        
        except BufferError:

            logger.warning("Local buffer is full, poll briefly and retry.")
            self.producer.poll(0.5)
            self.producer.produce(
                topic=topic,
                key=record_key,
                value=record_value,
                callback=self.delivery_report

            )

        except KafkaException as e:
            logger.error(f"Failed to produce message: {e}")


    def flush(self, timeout: float = 10.0):
        logger.info("Flushing pending messages before shutdown.")
        remaining = self.producer.flush(timeout)

        if remaining > 0:
            logger.warning(f"{remaining} message(s) still pending after timeout")
        else:
            logger.info("All of the messages were successfully delivered.")