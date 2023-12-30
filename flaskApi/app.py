from flask import Flask, Response, stream_with_context, request
import pandas as pd
from kdbSubs import *
from flask_cors import CORS
from qpython.qconnection import QConnection
import json
from waitress import serve


def create_app():
    app = Flask(__name__)
    CORS(app)
    kdb_host = "localhost"
    kdb_port = 5000

    @app.route('/pullData/<tbl>/<index>')
    def pullData(tbl,index):
        res = pd.DataFrame(sendKdbQuery('.gw.pullData', kdb_host, kdb_port, tbl, index))
        parseKdbTableWithSymbols(res)
        #parsing the times from integers on the frontend, if doing it on the python side use this next line
        #res['time'] = pd.to_datetime(res['time'], unit='ms').dt.strftime('%H:%M:%S.%f')
        result_dict = {}
        for column in res.columns:
            result_dict[column] = res[column].tolist()
        return result_dict


    @app.route('/pullData_options/<tbl>')
    def getIndexes(tbl):
        res = sendKdbQuery('.gw.getIndexes', kdb_host, kdb_port, tbl)
        res = parseKdbListWithSymbols(res)
        return res

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

    @app.route('/live')
    def tradeSub():
        tbl = request.args.get('tbl', 'trade')  # Get the parameter from the request
        index = request.args.get('index', 'TSLA')  # Get the parameter from the request
        qThread = kdbSub(tbl, index, kdb_host, kdb_port)
        qThread.start()
        return Response(
            stream_with_context(push_sse_events(qThread, tbl)),
            mimetype='text/event-stream'
        )
    
    return app

if __name__ == '__main__':
    app = create_app()
    serve(app, listen='*:8000')
