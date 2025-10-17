from AdminWrapper import KafkaAdmin
from pprint import pprint

def quick_test():
    """
    Quick test function demonstrating KafkaAdmin usage
    Run this to verify your Kafka setup
    """
    print("\n" + "="*70)
    print("KAFKA ADMIN - QUICK TEST")
    print("="*70 + "\n")
    
    # Initialize admin client
    admin = KafkaAdmin(
        bootstrap_servers='localhost:9094'
    )
    
    # Test 1: Create topics with different configurations
    # print("\n[TEST 1] Creating topics...")
    test_topics = ['test-topic-1', 'test-topic-2', 'test-topic-3']
    
    # results = admin.create_topics(
    #     topic_names=test_topics,
    #     num_partitions=3,
    #     replication_factor=1,
    #     retention_ms=604800000,  # 7 days
    #     compression_type='producer',
    #     cleanup_policy='delete',
    #     min_insync_replicas=1,
    #     max_message_bytes=1048576  # 1 MB
    # )
    # print(f"Creation results: {results}")
    
    # # Test 2: List all topics
    # print("\n[TEST 2] Listing topics...")
    # topics = admin.list_topics()
    # print(f"Available topics: {topics[:5]}...")  # Show first 5
    
    # Test 3: Add partitions
    # print("\n[TEST 3] Adding partitions...")
    # partition_results = admin.add_partitions_to_topic(
    #     topic_partitions={'test-topic-1': 5}  # Increase to 5 partitions
    # )
    # print(f"Partition addition results: {partition_results}")
    
    # # Test 4: Describe topic configuration
    # print("\n[TEST 4] Describing configurations...")
    # configs = admin.describe_topics_configs(
    #     resources=[('TOPIC', 'test-topic-1')],
    # )
    # pprint(f"Configurations: {configs}")

    # # Test 5: Clean up - Delete test topics
    print("\n[TEST 5] Cleaning up - Deleting test topics...")
    delete_results = admin.delete_topics(test_topics)
    print(f"Deletion results: {delete_results}")
    
    # print("\n" + "="*70)
    # print("TEST COMPLETED!")
    # print("="*70 + "\n")


if __name__ == "__main__":
    quick_test()