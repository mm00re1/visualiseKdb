from qconnect.qconnection import QConnection
import numpy as np
import threading
from queue import Queue
import select
import pandas as pd
import time

def sendKdbQuery(kdbFunction, host, port, *args):
    q = QConnection(host=host, port=port, tls_enabled=False, pandas = True)
    q.open()
    res = q.sendSync(kdbFunction, *args)
    if(isinstance(res, pd.DataFrame)):
        res = parse_dataframe(res)
    q.close() 
    return res

def query_kdb(q, function, *params):
    # try/except is teh catch the case where teh server has bounced and our q connection is stale
    try:
        return q.sendSync(function, *params)
    except Exception as e:
        # retry opening the conn only once, in case there is a different exception
        q.close()
        q.open()
        return q.sendSync(function, *params)

class kdbSub(threading.Thread):
    MAX_RETRIES = 5 # if unexpected error occurs during the subscription or message processing, attempt to resubscribe 5 times

    def __init__(self, kdb_host, kdb_port, *args):
        super(kdbSub, self).__init__()
        self.q = QConnection(host=kdb_host, port=kdb_port, tls_enabled=False, timeout = 10, pandas = True)
        self.params = args
        print("args: ", args)
        self.message_queue = Queue()
        self._stopper = threading.Event()
        self.retry_attempt = 0
        self.subscribe_to_kdb()

    def subscribe_to_kdb(self):
        # Attempt to (re)subscribe to kdb for live updates
        if self.retry_attempt >= self.MAX_RETRIES:
            print("Max retry attempts reached. Closing thread")
            self._stopper.set()
            return

        try:
            #Make sure connection is closed to avoid subscribing twice to the same kdb connection handle
            self.q.close()
            self.q.open()
            query_kdb(self.q, '.u.sub', *self.params)
            print("Subscribed to KDB successfully")
            self.retry_attempt = 0

        except Exception as e:
            print(f"Failed to subscribe to KDB: {e}")
            self.retry_attempt += 1
            time.sleep(2)
            self.subscribe_to_kdb()
        
    def stopit(self):
        print("KdbSubs - unsubbing")
        self._stopper.set()           # <--- signal thread first
        self.q.close()

    def stopped(self):
        return self._stopper.is_set()

    def run(self):
        try:
            while not self.stopped():
                try:
                    # Check if the socket has data ready to read with a timeout (1 second)
                    ready_to_read, _, _ = select.select([self.q._connection], [], [], 1.0)

                    # If data is available, read it
                    if ready_to_read:
                        message = self.q.receive(data_only=False, raw=False)
                        if isinstance(message.data, list):
                            if len(message.data) == 3 and message.data[0] == b'upd':
                                self.message_queue.put(parse_dataframe(message.data[2]))

                except Exception as e:
                    print("Error encountered while trying to read tick message: ", e)
                    self.subscribe_to_kdb()

        finally:
            try:
                self.q.close()
            except Exception as e:
                print("Error encountered while trying to close the kdb connection: ", e)

##utility functions##
def parseKdbTableWithSymbols(table):
    bstr_cols = table.select_dtypes([object]).columns
    for i in bstr_cols:
        table[i] = table[i].apply(lambda x: x.decode('latin'))

def parseKdbListWithSymbols(data):
    return [x.decode('latin') for x in data]

def parse_dataframe(data):
    df_data = data.to_dict(orient='records')
    df_columns = list(data.columns)
    return {"columns": df_columns, "rows": clean_data(df_data), "num_rows": len(data)}

def clean_data(data):
    # clean data recursively - replacing Nan or Inf with None
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(v) for v in data]
    elif isinstance(data, bytes):
        return data.decode('utf-8')
    elif isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
        return None
    elif pd.isna(data):
        return None
    return data
