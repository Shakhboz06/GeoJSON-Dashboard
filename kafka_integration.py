from kafka import KafkaProducer  # Imports KafkaProducer from the kafka-python library for producing messages
import json                     # Imports json to handle serialization of Python objects to JSON strings
import logging                # Imports logging to record info and errors

def get_kafka_producer(bootstrap_servers='kafka:9092'):
    
    # Initializes and returns a KafkaProducer instance:
    # Parameters:
    #  - bootstrap_servers (str): The Kafka bootstrap server address (default is 'kafka:9092').
    # Returns:
    # - A KafkaProducer instance if successful, or None if initialization fails.

    
    try:
        # Creates a KafkaProducer instance with the specified bootstrap servers.
        # The value_serializer converts Python objects to JSON-encoded bytes.
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        # Log a success message if the producer is initialized properly.
        logging.info("Kafka producer initialized successfully.")
        return producer  # Return the producer instance for further use.
    except Exception as e:
        # Log any exception encountered during initialization and return None.
        logging.error(f"Error initializing Kafka producer: {e}")
        return None

def send_kafka_event(producer, topic, event):
    
    # Send an event to the specified Kafka topic.
    # Parameters: producer: A KafkaProducer instance.
    #   - topic (str): The Kafka topic to which the event will be sent.
    # event (dict): The event data to send (will be serialized to JSON).
    
    if producer is None:
        # If the producer is not initialized, log an error and exit the function.
        logging.error("Kafka producer is not initialized.")
        return

    try:
        # Sending the event to the given topic.
        producer.send(topic, event)
        # Flushing ensures that the message is actually sent out immediately.
        producer.flush()  # Ensuring the event is sent
        # Loggs the event that was sent for debugging/confirmation.
        logging.info(f"Kafka event sent: {event}")
    except Exception as e:
        # Logs any exception that might occur during the sending of the event.
        logging.error(f"Error sending Kafka event: {e}")
