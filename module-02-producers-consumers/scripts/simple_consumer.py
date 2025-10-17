from confluent_kafka import Consumer, KafkaError

broker = "localhost:9094"

group_id = "demo-group"

consumer = Consumer({

    'bootstrap.servers': broker,
    'group.id': group_id,
    'auto.offset.reset': 'earliest'
})

consumer.subscribe(['demo-topic'])

while True:

    msg = consumer.poll(1.0)

    if msg is None:
        continue

    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        else:
            print(f"Consumer error: {msg.error()}")
            continue
    
    print(msg.value())
    print(msg.value().decode())

    