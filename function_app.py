import azure.functions as func
import datetime
import json
import logging
import time

app = func.FunctionApp()

def process_with_retries(event_data, max_retries=3):
    """Manual retry logic for event processing"""
    for attempt in range(max_retries):
        try:
            body = json.loads(event_data)
            timestamp = body.get("timestamp", "N/A")
            temp = body.get("temperature", "N/A")
            occupancy = body.get("occupancy", "N/A")
            
            logging.info(f"[{timestamp}] Data from parking-system -> Temp: {temp}°C | Occupancy: {occupancy}")
            return True
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            logging.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
            time.sleep(wait_time)

@app.function_name(name="iot-hub-trigger")
@app.event_hub_message_trigger(
    arg_name="event",
    event_hub_name="iothub-ehub-soil-moist-63534805-bc73aff3db", 
    connection="IOT_HUB_CONNECTION_STRING",
    consumer_group="parking"
)
def main(event: func.EventHubEvent):
    try:
        logging.info("Function triggered by Event Hub message")
        process_with_retries(event.get_body().decode('utf-8'))
        
    except Exception as e:
        logging.error(f"All retries failed: {str(e)}")
        logging.error(f"Raw event data: {event.get_body().decode('utf-8')}")