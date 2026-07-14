"""
Kafka-based mock data generator — simulates Double-11 order traffic and pageviews.
Produces high-concurrency events to Kafka topics for Flink consumption.
"""
import json
import time
import random
import uuid
import sys
from datetime import datetime

try:
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable
except ImportError:
    print("[!!]️  kafka-python not installed. Install with: pip install kafka-python")
    sys.exit(1)

PRODUCTS = [
    ("iPhone 15 Pro Max", "electronics", 8999.00),
    ("MacBook Air M3", "electronics", 10999.00),
    ("AirPods Pro", "electronics", 1899.00),
    ("iPad Air", "electronics", 4799.00),
    ("Apple Watch S9", "electronics", 3199.00),
    ("Nike Air Max", "sports", 899.00),
    ("Adidas Ultraboost", "sports", 1099.00),
    ("Lululemon Yoga Pants", "sports", 599.00),
    ("North Face Jacket", "sports", 1599.00),
    ("YSL Lipstick", "beauty", 380.00),
    ("Estee Lauder Serum", "beauty", 890.00),
    ("SK-II Facial Essence", "beauty", 1299.00),
    ("Dyson Vacuum V15", "home", 4999.00),
    ("IKEA Standing Desk", "home", 2499.00),
    ("Philips Air Purifier", "home", 1999.00),
    ("Nintendo Switch OLED", "games", 2299.00),
    ("PS5 Slim", "games", 3499.00),
    ("LEGO Star Wars", "games", 699.00),
    ("Moutai Feitian 53", "liquor", 1499.00),
    ("Tsingtao Beer 24-pack", "liquor", 89.00),
]

PAGES = [
    "/", "/search", "/cart", "/checkout",
    "/product/iphone15", "/product/macbook", "/product/airpods",
    "/product/nike", "/product/lululemon", "/product/dyson",
    "/category/electronics", "/category/sports", "/category/beauty",
    "/category/home", "/category/games", "/promo/double11",
]


def generate_order():
    product = random.choice(PRODUCTS)
    return {
        "orderId": str(uuid.uuid4()),
        "userId": f"user_{random.randint(1, 500000)}",
        "productId": f"prod_{PRODUCTS.index(product)}",
        "productName": product[0],
        "category": product[1],
        "price": product[2],
        "quantity": random.choices([1, 2, 3, 4, 5], weights=[60, 25, 10, 3, 2])[0],
        "timestamp": int(time.time() * 1000),
    }


def generate_pageview():
    return {
        "userId": f"user_{random.randint(1, 500000)}",
        "page": random.choice(PAGES),
        "timestamp": int(time.time() * 1000),
    }


def create_kafka_producer(bootstrap_servers):
    """Create a Kafka producer with retry logic."""
    for attempt in range(10):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                batch_size=16384,
                linger_ms=5,
                compression_type="gzip",
                max_request_size=1048576,
                retries=3,
            )
            print(f"[OK] Kafka producer connected to {bootstrap_servers}")
            return producer
        except NoBrokersAvailable:
            print(f"[Wait] Waiting for Kafka broker at {bootstrap_servers}... (attempt {attempt + 1}/10)")
            time.sleep(3)
    raise RuntimeError(f"Cannot connect to Kafka at {bootstrap_servers}")


def stream_to_kafka(producer, topic, gen_func, rate_per_sec, name):
    """
    Produce events to a Kafka topic at the specified rate.
    Uses burst mode (5% chance) to simulate flash-sale traffic spikes.
    """
    interval = 1.0 / rate_per_sec if rate_per_sec > 0 else 0
    count = 0
    last_report = time.time()
    next_send = time.time()
    batch = []

    print(f"[{name}] Producing to topic '{topic}' at ~{rate_per_sec} events/sec")
    print(f"         (5%% burst chance: 3x-8x traffic spike)")

    try:
        while True:
            now = time.time()

            # Burst mode (5% chance) — simulates flash-sale spikes
            burst = 1.0
            if random.random() < 0.05:
                burst = random.uniform(3, 8)

            # Generate events for this tick
            while now >= next_send:
                batch.append(gen_func())
                count += 1
                next_send += interval / burst
                if next_send < now:
                    next_send = now

            # Flush batch to Kafka
            if batch:
                for record in batch:
                    producer.send(topic, value=record)
                producer.flush()
                batch.clear()

            # Report stats every 5 seconds
            if now - last_report >= 5:
                rate = count / (now - last_report) if now > last_report else 0
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {name}: {count} total | ~{rate:.0f}/s")
                last_report = now
                count = 0

            time.sleep(0.001)
    except KeyboardInterrupt:
        pass
    finally:
        producer.close()


def main():
    orders_per_sec = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    pv_per_sec = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    kafka_broker = sys.argv[3] if len(sys.argv) > 3 else "localhost:9092"

    print("=" * 60)
    print("  [Cart] E-commerce Data Generator (Kafka Mode)")
    print("=" * 60)
    print(f"  Kafka Broker:  {kafka_broker}")
    print(f"  Orders:        {orders_per_sec}/s → topic 'order-events'")
    print(f"  PageViews:     {pv_per_sec}/s → topic 'pageview-events'")
    print(f"  Burst Mode:    5% chance, 3x-8x traffic spike")
    print("=" * 60)
    print()

    producer = create_kafka_producer(kafka_broker)

    import threading
    t1 = threading.Thread(
        target=stream_to_kafka,
        args=(producer, "order-events", generate_order, orders_per_sec, "ORDERS"),
        daemon=True,
    )
    t2 = threading.Thread(
        target=stream_to_kafka,
        args=(producer, "pageview-events", generate_pageview, pv_per_sec, "PAGEVIEWS"),
        daemon=True,
    )

    t1.start()
    t2.start()

    try:
        while t1.is_alive() or t2.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Stop] Shutting down...")


if __name__ == "__main__":
    main()
