from qpython.qconnection import QConnection
import numpy
import threading
from qpython.qtype import QException
from qpython.qcollection import QTable
from queue import Queue
import select

def sendKdbQuery(kdbFunction, host, port, *args):
    q = QConnection(host=host, port=port, tls_enabled=False)
    q.open()
    res = q.sendSync(kdbFunction, *args)
    q.close() 
    return res

class kdbSub(threading.Thread):
    def __init__(self, tbl, index, kdb_host, kdb_port):
        super(kdbSub, self).__init__()
        self.q = QConnection(host=kdb_host, port=kdb_port, tls_enabled=False)
        self.q.open()
        self.q.sendSync('.u.sub', numpy.bytes_(tbl), numpy.bytes_(index))
        self.message_queue = Queue()
        self._stopper = threading.Event()

    def stopit(self):
        print("KdbSubs - unsubbing")
        self._stopper.set()           # <--- signal thread first
        ###self.q.sendAsync(".u.unsub","direct unsub")  --> unsub logic is also handled in .z.pc

    def stopped(self):
        return self._stopper.is_set()

    def run(self):
        try:
            while not self.stopped():
                # Check if the socket has data ready to read with a timeout (1 second)
                ready_to_read, _, _ = select.select([self.q._connection], [], [], 1.0)

                # If data is available, read it
                if ready_to_read:
                    message = self.q.receive(data_only=False, raw=False)
                    if isinstance(message.data, list):
                        if len(message.data) == 3 and message.data[0] == b'upd' and isinstance(message.data[2], QTable):
                            for row in message.data[2]:
                                self.message_queue.put(row)
                else:
                    # No data received within the timeout, continue looping
                    #print("No data received, checking stop condition...")
                    continue

        except Exception as e:
            print("Error encountered while trying to read tick message: ", e)
        finally:
            print("KdbSubs - closing the connection")
            self.q.close()
            print("KdbSubs - finished closing conn")

##utility functions##
def parseKdbTableWithSymbols(table):
    bstr_cols = table.select_dtypes([object]).columns
    for i in bstr_cols:
        table[i] = table[i].apply(lambda x: x.decode('latin'))

def parseKdbListWithSymbols(data):
    return [x.decode('latin') for x in data]
