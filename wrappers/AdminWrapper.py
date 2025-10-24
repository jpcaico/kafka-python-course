from confluent_kafka.admin import AdminClient, NewPartitions, NewTopic, ConfigResource
from confluent_kafka import KafkaException
import logging
from typing import List, Dict, Optional, Union


# set up our log config

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class KafkaAdmin:

    def __init__(self, bootstrap_servers: Union[str, List[str]], **config):

        """
        bootstrap_servers: host:port or list of host:port
        **config: any extra configuiration properties that we might want to pass
        """

        if isinstance(bootstrap_servers, list):
            bs = ",".join(bootstrap_servers)
        else:
            bs = str(bootstrap_servers)

        self.config = {
            'bootstrap.servers' : bs,
            'socket.timeout.ms': 10000,
            'request.timeout.ms': 15000 

        }

        self.config.update(config)

        self.admin_client = AdminClient(self.config)

        logger.info(f"Kafka Admin initialized with brokers: {bs}")


    def create_topics(
            self,
            topic_names: List[str],
            num_partitions: int = 3,
            replication_factor: int = 1,
            retention_ms: Optional[int] = None,
            cleanup_policy: str = 'delete',
            min_insync_replicas: int = 1,
            compression_type: str = 'producer',
            max_message_bytes: Optional[int] = None

    ) -> Dict[str, bool]:
        
        topic_config = {}

        if retention_ms is not None:
            topic_config['retention.ms'] = str(retention_ms)

        if cleanup_policy:
            topic_config['cleanup.policy'] = cleanup_policy

        if compression_type:
            topic_config['compression.type'] = compression_type

        if max_message_bytes is not None:
            topic_config['max.message.bytes'] = str(max_message_bytes)

        if min_insync_replicas is not None:
            topic_config['min.insync.replicas'] = str(min_insync_replicas)


        new_topics = [
            NewTopic(
                topic = t,
                num_partitions = num_partitions,
                replication_factor = replication_factor,
                config = topic_config
            )
            for t in topic_names
        ]

        futures = self.admin_client.create_topics(new_topics)

        results: Dict[str, bool] = {}

        for topic, fut in futures.items():
            try:
                fut.result()
                logger.info(f"Topic {topic} create successfully")
                results[topic] = True
            except KafkaException as e:
                logger.error(f"Failed to create topic {topic}: {e}")
                results[topic] = False

        return results


    def list_topics(self) -> List[str]:

        topic_metadata = self.admin_client.list_topics(timeout=10)

        topics = list(topic_metadata.topics.keys())

        logger.info(f"Retrieved topics from cluster: {topics}")

        return topics
    

    def add_partitions_to_topic(
            
            self, 
            topic_partitions: Dict[str, int]
    ) -> Dict[str, bool]:
        
        new_partitions = [NewPartitions(topic, new_count) for topic, new_count in topic_partitions.items()]

        futures = self.admin_client.create_partitions(
            new_partitions
        )

        results: Dict[str, bool] = {}

        for topic, fut in futures.items():

            try:
                fut.result()
                logger.info(f"Partitions added successfully to topic: {topic}")
                results[topic] = True
            except KafkaException as e:
                logger.error(f"Failed to add partitions to topic: {topic}: {e}")
                results[topic] = False

        return results
    

    def describe_topics_configs(
            self,
            resources: List[tuple]
    ) -> Dict[str, Dict]:
        
        config_resources = [
            ConfigResource(resource_type, resource_name) for resource_type, resource_name in resources
        ]

        futures = self.admin_client.describe_configs(config_resources)

        results: Dict[str, Dict] = {}

        for resource, fut in futures.items():
            try:
                config = fut.result()

                results[str(resource)] = {}

                for config_name, config_entry in config.items():
                    results[str(resource)][config_name] = config_entry.value

                logger.info(f"Configs for {resource}")

            except KafkaException as e:
                logger.error(f"Failed to describe configs for {resource.name}: {e}")

        return results
    

    def delete_topics(
        self,
        topic_names: List[str]
    ) -> Dict[str, bool]:

        futures = self.admin_client.delete_topics(topic_names)

        results: Dict[str, bool] = {}


        for topic, fut in futures.items():
            try:

                fut.result()
                logger.info(f"Topic '{topic}' deleted successfully")
                results[topic] = True
            except KafkaException as e:

                logger.error(f"Failed to delete topic '{topic}': {e}")
                results[topic] = False

        return results