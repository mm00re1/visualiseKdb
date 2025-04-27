from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from queue import Empty
import pandas as pd
from kdbSubs import *
import json
import asyncio
import uvicorn
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kdb_host = "localhost"
kdb_port = 5000

def make_json_serializable(data):
    """Recursively convert non-serializable objects in the data to JSON-friendly types."""
    if isinstance(data, dict):
        # Convert each value in the dictionary
        return {key: make_json_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        # Convert each element in the list
        return [make_json_serializable(element) for element in data]
    elif isinstance(data, pd.Timedelta):
        # Convert Timedelta to string (or seconds if you prefer)
        return str(data).split(" ")[-1]
    elif hasattr(data, 'item'):  # Handles numpy types like np.int32, np.float64
        return data.item()
    else:
        return data

@app.get("/pullData/{tbl}/{index}")
async def pull_data(tbl: str, index: str):
    data = sendKdbQuery('.gw.pullData', kdb_host, kdb_port, tbl, index)
    json_data = make_json_serializable(data)
    return json_data

@app.get("/pullData_options/{tbl}")
async def get_indexes(tbl: str):
    res = sendKdbQuery('.gw.getIndexes', kdb_host, kdb_port, tbl)
    res = parseKdbListWithSymbols(res)
    return res

@app.websocket("/live")
async def trade_sub_ws(websocket: WebSocket):
    #    Example the client can connect with: ws://localhost:8000/live?tbl=trade&index=TSLA
    await websocket.accept()
    print(f"Active threads: {threading.active_count()}")
    
    tbl = websocket.query_params.get('tbl', 'trade')
    index = websocket.query_params.get('index', 'TSLA')

    # Create the subscription thread with *args
    qThread = kdbSub(kdb_host, kdb_port, tbl, index)
    qThread.start()
    keepalive_counter = 0

    try:
        while True:
            if qThread.stopped():
                break

            # Drain the queue to get the latest message, we discard the earlier messages
            latest_data = None
            while True:
                try:
                    latest_data = qThread.message_queue.get_nowait()
                except Empty:
                    break

            if latest_data:
                try:
                    # Convert numpy types to Python native types (e.g., int, float)
                    serializable_data = make_json_serializable(latest_data)
                    json_data = json.dumps(serializable_data)
                    await websocket.send_text(json_data)
                except Exception as e:
                    # Log any unexpected serialization errors
                    print(f"Error serializing data: {e}")

            else:
                keepalive_counter += 1
                if keepalive_counter >= 50:  # e.g. every ~5 second if each loop is 0.1s
                    # Force a send that fails if the socket is closed
                    await websocket.send_text("KEEPALIVE")
                    keepalive_counter = 0

                # Yield control back to the event loop briefly
                await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        print(f"Unhandled WebSocket error: {e}")
    finally:
        # Clean up the subscription thread
        qThread.stopit()
        print("finished the stopit")


'''   # SSE Approach defined below
def push_sse_events(listener_thread, tbl):
    try:
        while not listener_thread.stopped():
            data = listener_thread.message_queue.get()
            if tbl == 'trade':
                json_data = json.dumps({
                    'time': int(data[0]),
                    'price': data[1]
                })
            else:
                json_data = json.dumps({
                    'time': int(data[0]),
                    'bid': data[1],
                    'ask': data[2]
                })
            yield f"data: {json_data}\n\n"
    except GeneratorExit:
        print("Client disconnected, stopping the listener thread.")
        listener_thread.stopit()

@app.get("/live")
async def trade_sub(request: Request, tbl: str = 'trade', index: str = 'TSLA'):
    qThread = kdbSub(tbl, index, kdb_host, kdb_port)
    qThread.start()
    return StreamingResponse(push_sse_events(qThread, tbl), media_type="text/event-stream")
'''

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
