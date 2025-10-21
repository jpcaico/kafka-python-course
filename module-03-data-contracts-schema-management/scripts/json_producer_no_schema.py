from confluent_kafka import Producer
import json

broker = "localhost:9094"

p = Producer({'bootstrap.servers': broker})
topic_name = 'demo-topic'

# v1

# event_v1 = {"user_id": 42, "event": "login", "timestamp": 1733365454}
# p.produce(topic=topic_name, value=json.dumps(event_v1))
# p.flush()

# v2
event_v2 = {"uid": 42, "meta": {"name": "login"}, "timestamp": 1733635423}
p.produce(topic=topic_name, value=json.dumps(event_v2))
p.flush()