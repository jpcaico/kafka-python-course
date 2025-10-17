from confluent_kafka import Producer

broker = "localhost:9094"

p = Producer({'bootstrap.servers': broker})

topic_name = 'demo-topic'

try:

    while True:
        line = input("kafka>").strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break


        p.produce(topic = topic_name, value = line)

        p.poll(0)

except (KeyboardInterrupt, EOFError):
    print()


print("Flushing pending messages..")
p.flush()