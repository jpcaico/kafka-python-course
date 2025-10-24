import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wrappers.AdminWrapper import KafkaAdmin
import yaml

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("setup-topics")

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
    

def setup_topics():

    config = load_config()

    bootstrap_servers = config['kafka']['bootstrap_servers']

    logger.info(f"Initializing Kafka Admin with brokers: {bootstrap_servers}")

    admin = KafkaAdmin(bootstrap_servers=bootstrap_servers)

    topic_name = config['kafka']['topics']['purchases']

    logger.info(f"Creating topic: {topic_name}")
    logger.info(f"Partitions = 3")
    logger.info(f"Replication factor = 3")
    logger.info(f"Min ISR = 2")
    logger.info(f"Retention = 7 days")

    results = admin.create_topics(
        topic_names=[topic_name],
        num_partitions=3,
        replication_factor=3,
        retention_ms=7 * 24*60*60*1000,
        cleanup_policy='delete',
        min_insync_replicas=2,
        compression_type='snappy'

    )

    if results and results.get(topic_name):
        logger.info(f"Topic {topic_name} created successfully")
    else:
        logger.info(f"Topic {topic_name} created (or already exists)")

    
    logger.info("\n Listing all topics in cluster")
    all_topics = admin.list_topics()

    for topics in all_topics:
        if not topics.startswith('_'):
            logger.info(f" - {topics}")


    logger.info(f"Topic configuration details for {topic_name}")

    configs = admin.describe_topics_configs([('TOPIC', topic_name)])

    if configs:
        config_key = list(configs.keys())[0]  
        topic_config = configs.get(config_key, {})
        important_configs = [
            'retention.ms',
            'cleanup.policy',
            'min.insync.replicas',
            'replication.factor',
            'compression.type',
            'max.message.bytes'
        ]

        for config_key in important_configs:
            if config_key in topic_config:
                logger.info(f" - {config_key}: {topic_config[config_key]}")


if __name__ == "__main__":
    try:
        setup_topics()
    except Exception as e:
        logger.error(f"Failed to setup topics: {e}")
        sys.exit(1)
        