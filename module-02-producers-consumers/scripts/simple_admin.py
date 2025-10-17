from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException

broker = "localhost:9094"
topic = "demo-topic"
num_partitions = 1
replication_factor = 1

admin = AdminClient({"bootstrap.servers": broker})

new_topic = NewTopic(
topic=topic,
num_partitions = num_partitions,
replication_factor = replication_factor

)

futures = admin.create_topics([new_topic])

for t, f in futures.items():
    try:
        f.result()
        print(f"Created topic {t} successfully.")
    except Exception as e:
        print(f"Failed do create '{t}': {e}")


# solution for delete topic
# futures = admin.delete_topics([topic])

# for t, f in futures.items():
#     try:
#         f.result() 
#         print(f"Topic '{t}' deleted successfully.")
#     except Exception as e:
#         print(f"Failed to delete '{t}': {e}")