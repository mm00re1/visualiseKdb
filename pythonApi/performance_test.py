import asyncio
import websockets
import threading
import time
import json
from datetime import datetime
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Shared dictionary to store tables from each thread
results = {}
# Lock to ensure thread-safe access to results
results_lock = threading.Lock()

async def websocket_client(client_id, duration=60):
    """Run a WebSocket client that connects to the server and collects messages."""
    uri = "ws://localhost:8000/live?tbl=quote&index=TSLA"
    table = []  # List to store messages for this client
    start_time = time.time()

    try:
        async with websockets.connect(uri) as ws:
            logger.info(f"Client {client_id} connected to {uri}")
            while time.time() - start_time < duration:
                try:
                    # Receive message with a timeout to check duration
                    message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    timestamp = datetime.now().isoformat()
                    is_keepalive = message == "KEEPALIVE"
                    table.append({
                        'timestamp': timestamp,
                        'is_keepalive': is_keepalive,
                        'message': message if not is_keepalive else None  # Optional: store message content
                    })
                    logger.debug(f"Client {client_id} received {'KEEPALIVE' if is_keepalive else 'data'} at {timestamp}")
                except asyncio.TimeoutError:
                    continue  # Timeout means no message, check duration
                except websockets.exceptions.ConnectionClosed:
                    logger.warning(f"Client {client_id} connection closed")
                    break
                except Exception as e:
                    logger.error(f"Client {client_id} error: {e}")
                    break

    except Exception as e:
        logger.error(f"Client {client_id} failed to connect or run: {e}")

    # Convert table to DataFrame and store in results
    df = pd.DataFrame(table)
    with results_lock:
        results[client_id] = df
    logger.info(f"Client {client_id} finished with {len(df)} messages")

def run_client_in_thread(client_id, duration=60):
    """Run the WebSocket client in a dedicated asyncio event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(websocket_client(client_id, duration))
    finally:
        loop.close()

def main():
    """Spawn 20 threads, each running a WebSocket client, and collect results."""
    duration = 60  # Run for 60 seconds
    threads = []
    num_clients = 20
    thread_starts = {}

    # Start 20 threads
    logger.info(f"Starting {num_clients} WebSocket clients")
    for i in range(num_clients):
        client_id = f"client_{i}"
        thread = threading.Thread(target=run_client_in_thread, args=(client_id, duration))
        thread.daemon = True  # Ensure threads exit when main process exits
        threads.append(thread)
        thread.start()
        thread_starts[client_id] = time.time()
        time.sleep(0.2)

    # Wait for duration or until all threads finish
    start_time = time.time()
    i = 0
    for thread in threads:
        client_id = f"client_{i}"
        remaining_time = duration - (time.time() - thread_starts[client_id])
        if remaining_time > 0:
            thread.join(timeout=remaining_time)
        i+=1

    # Summarize results
    logger.info("Test completed. Summarizing results...")
    with results_lock:
        for client_id, df in results.items():
            keepalive_count = len(df[df['is_keepalive']])
            data_count = len(df[~df['is_keepalive']])
            logger.info(f"{client_id}: {len(df)} messages (Keepalive: {keepalive_count}, Data: {data_count})")
            # Optionally save to CSV
            df.to_csv(f"{client_id}_messages.csv", index=False)

    # Example: Access a specific client's table
    if 'client_0' in results:
        logger.info(f"Sample table for client_0:\n{results['client_0'].head().to_string()}")

if __name__ == "__main__":
    main()
