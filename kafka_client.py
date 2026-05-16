# kafka_client.py
from kafka import KafkaProducer, KafkaConsumer
import json
from threading import Event


class KafkaProducerClient:
    def __init__(self, kafka_server="localhost:9092", topic="article_topic"):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_server,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = topic

    def send_article(self, article):
        """Send article to Kafka topic."""
        if article:
            self.producer.send(self.topic, value=article)
            #print(f"Sent article: {article['title']} to Kafka.")

    def close(self):
        """Flush and close Kafka producer."""
        self.producer.flush()
        self.producer.close()


class KafkaConsumerClient:
    def __init__(self, kafka_server="localhost:9092", topic="article_topic"):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_server,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            enable_auto_commit=True,
            group_id="article_group"  # Optional: for consumer group management
        )
        self.stop_event = Event()


    def consume_articles(self):
        """Consume articles from Kafka with a timeout to allow stopping."""
        print("Consumer started.")
        while not self.stop_event.is_set():
            # Poll for new messages with a timeout of 1 second
            for message in self.consumer:
                article = message.value
                print(f"Consumed article: {article['title']}")
            # Sleep for a short duration to avoid busy-waiting
            time.sleep(1)

    def stop_consuming(self):
        """Set the stop event to gracefully stop the consumer."""
        self.stop_event.set()
        self.consumer.close()