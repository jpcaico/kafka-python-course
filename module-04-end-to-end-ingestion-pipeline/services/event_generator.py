import sys
import logging
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from faker import Faker
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry.avro import AvroSerializer

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wrappers.ProducerWrapper import KafkaProducer
from wrappers.SchemaRegistryWrapper import SchemaRegistryAdmin

import yaml

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
    

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("event-generator")


fake = Faker()


class PurchaseEventGenerator:

    def __init__(self, config: Dict[str, Any]):

        self.config = config
        self.regions = list(config['regions'].keys())
        self.products = config['product']

        logger.info(f"Event generator initialized with {len(self.regions)} regions")
        logger.info(f"Number of available products: {len(self.products)}")


    def generate_purchase_event(self, region: str) -> Dict[str, Any]:

        product = random.choice(self.products)
        user_id_min, user_id_max = self.config['event_generation']['user_id_range']
        amount_min, amount_max = self.config['event_generation']['amount_range']

        event = {

            'event_id': str(uuid4()),
            'user_id': random.randint(user_id_min, user_id_max),
            'region': region,
            'product_id': product['id'],
            'product_name': product['name'],
            'quantity': random.randint(1,5),
            'amount': round(random.uniform(amount_min, amount_max), 2),
            'currency': self.config['regions'][region]['currency'],
            'timestamp': int(datetime.now().timestamp() * 1000)

        }

        return event
    
def load_schema(schema_name: str) -> str:

    schema_path = Path(__file__).parent.parent / "schemas" / f"{schema_name}.avsc"

    try:
        with open(schema_path, 'r') as f:
            schema_str = f.read()
            logger.info(f"Schema loaded for serialization: {schema_name}")
            return schema_str
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        logger.error(f"Run the schema verification first!")
        sys.exit(1)



def main():

    config = load_config()

    schema_admin = SchemaRegistryAdmin(url=config['kafka']['schema_registry_url'])

    event_generator = PurchaseEventGenerator(config)

    schema_str = load_schema('purchase_event')

    topic_name = config['kafka']['topics']['purchases']

    subject_name = f"{topic_name}-value"

    logger.info(f"Registering the schema for subject {subject_name}")
    registration_info = schema_admin.register_avro(subject_name, schema_str)

    if not registration_info:
        logger.error("Schema registration failed")
        sys.exit(1)

    schema_id = registration_info.get("id")
    logger.info(f"Schema registered with ID: {schema_id}")

    key_serializer = StringSerializer('utf_8')
    value_serializer = AvroSerializer(
        schema_registry_client = schema_admin.client,
        schema_str = schema_str,
        to_dict = lambda obj, ctx: obj
    )


    bootstrap_servers = ','.join(config['kafka']['bootstrap_servers'])

    producer = KafkaProducer(
        bootstrap_servers= bootstrap_servers,
        client_id = 'purchase-event-producer'
    )

    logger.info(f"Producer initialized with brokers: {bootstrap_servers}")

    events_per_second = config['event_generation']['events_per_second']
    sleep_time = 1.0 / events_per_second

    logger.info(f"Starting event generation: {events_per_second} events/second")
    logger.info(f"Press Ctrl + C to stop the producer")

    event_count = 0

    try:
        while True:

            region = random.choice(event_generator.regions)
            event = event_generator.generate_purchase_event(region)

            key = str(event['user_id'])

            serialized_key = key_serializer(key)
            serialized_value = value_serializer(
                event,
                SerializationContext(topic_name, MessageField.VALUE)
            )

            producer.produce_message(
                topic_name,
                key=serialized_key,
                value=serialized_value
            )

            event_count += 1

            if event_count % 10 == 0:
                logger.info(

                    f"Produced {event_count} events |"
                    f"Last: region {region} user={event['user_id']}" 
                    f"product={event['product_name']}"
                    f"amount={event['amount']} {event['currency']}"

                )

            time.sleep(sleep_time)
    except KeyboardInterrupt:
        logger.info(f"Stopping producer...")
        logger.info(f"Total events produced: {event_count}")

    finally:
        logger.info(f"Flushing remaining messages...")
        producer.flush()


if __name__ == "__main__":
    main()


