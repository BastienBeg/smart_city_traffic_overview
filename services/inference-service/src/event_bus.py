"""
Kafka Event Bus module for publishing detection events.
"""
import json
import logging
import os
from typing import Any, Dict, Optional
from confluent_kafka import Producer

logger = logging.getLogger("EventBus")


class KafkaEventBus:
    """
    Kafka producer wrapper for publishing detection events.
    """

    def __init__(self, bootstrap_servers: Optional[str] = None, topic: str = "events.detections"):
        """
        Initializes the Kafka producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers (e.g., "localhost:9092").
                               Defaults to KAFKA_BOOTSTRAP_SERVERS env var.
            topic: Kafka topic to publish to.
        """
        self.bootstrap_servers = bootstrap_servers or os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.topic = topic
        self.producer: Optional[Producer] = None
        logger.info(f"Initialized KafkaEventBus targeting {self.bootstrap_servers}, topic={self.topic}")

    def connect(self) -> bool:
        """
        Creates the Kafka producer.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            self.producer = Producer({
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "inference-service",
                "acks": "all",
            })
            logger.info(f"Kafka producer created for {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            return False

    def _delivery_report(self, err, msg):
        """Callback for delivery reports."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

    def publish(self, event: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        Publishes a detection event to the Kafka topic.

        Args:
            event: The detection event dictionary to publish.
            key: Optional message key (e.g., camera_id).

        Returns:
            True if message was enqueued successfully, False otherwise.
        """
        if not self.producer:
            logger.error("Producer not connected. Call connect() first.")
            return False

        try:
            message = json.dumps(event).encode("utf-8")
            key_bytes = key.encode("utf-8") if key else None
            self.producer.produce(
                self.topic,
                value=message,
                key=key_bytes,
                callback=self._delivery_report,
            )
            # Trigger any available delivery callbacks (non-blocking)
            self.producer.poll(0)
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    def flush(self, timeout: float = 5.0):
        """Flush pending messages to Kafka."""
        if self.producer:
            self.producer.flush(timeout)

    def close(self):
        """Close the producer."""
        if self.producer:
            self.producer.flush(10)
            logger.info("Kafka producer closed.")
