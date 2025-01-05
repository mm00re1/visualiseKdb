from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from queue import Empty
import pandas as pd
from kdbSubs import *
from qpython.qconnection import QConnection
import json
import asyncio

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

@app.get("/pullData/{tbl}/{index}")
async def pull_data(tbl: str, index: str):
    res = pd.DataFrame(sendKdbQuery('.gw.pullData', kdb_host, kdb_port, tbl, index))
    parseKdbTableWithSymbols(res)
    #parsing the times from integers on the frontend, if doing it on the python side use this next line
    #res['time'] = pd.to_datetime(res['time'], unit='ms').dt.strftime('%H:%M:%S.%f')
    result_dict = {column: res[column].tolist() for column in res.columns}
    return result_dict

@app.get("/pullData_options/{tbl}")
async def get_indexes(tbl: str):
    res = sendKdbQuery('.gw.getIndexes', kdb_host, kdb_port, tbl)
    res = parseKdbListWithSymbols(res)
    return res

@app.websocket("/live")
async def trade_sub_ws(websocket: WebSocket):
    """
    WebSocket endpoint. 
    The client can connect with: ws://localhost:8000/live?tbl=trade&index=TSLA
    """
    await websocket.accept()

    # Extract query params from the WebSocket URL
    tbl = websocket.query_params.get('tbl', 'trade')
    index = websocket.query_params.get('index', 'TSLA')

    # Spin up the subscription thread
    qThread = kdbSub(tbl, index, kdb_host, kdb_port)
    qThread.start()

    try:
        while not qThread.stopped():
            try:
                # Attempt to get data without blocking:
                data = qThread.message_queue.get_nowait()
            except Empty:
                # No data right now, so let the event loop run briefly
                await asyncio.sleep(0.01)
                continue

            # Convert row to JSON
            if tbl == 'trade':
                json_data = json.dumps({
                    'time': int(data[0]),
                    'price': data[1],
                })
            else:
                json_data = json.dumps({
                    'time': int(data[0]),
                    'bid': data[1],
                    'ask': data[2],
                })

            # Send to client
            await websocket.send_text(json_data)

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        print(f"Unhandled WebSocket error: {e}")
    finally:
        # Clean up the subscription thread
        qThread.stopit()

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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
