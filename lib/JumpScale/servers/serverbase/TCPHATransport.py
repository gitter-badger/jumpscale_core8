from JumpScale import j
from servers.serverbase.DaemonClient import Transport
import time

def retry(func):
    def wrapper(self, *args, **kwargs):
        try:
            if j.sal.nettools.tcpPortConnectionTest(*self._connection[:2]):
                clientfunc = getattr(self._client, func.__name__)
                return clientfunc(*args, **kwargs)
        except:
            pass # we will execute the reconnect
        self._connection[2] = time.time()
        self.connect(self._id)
        clientfunc = getattr(self._client, func.__name__)
        return clientfunc(*args, **kwargs)
    return wrapper

class TCPHATransport(Transport):
    def __init__(self, connections, clientclass, *args, **kwargs):
        self._connections = [ [ip, port, 0] for ip, port in connections ]
        self._timeout = 60
        self._args = args
        self._kwargs = kwargs
        self._clientclass = clientclass
        self._client = None
        self._connection = None
        self._id = None

    def connect(self, sessionid):
        if self._client:
            self._client.close()
        for attempt in range(2):
            for connection in sorted(self._connections, key=lambda c: c[-1]):
                try:
                    if j.sal.nettools.tcpPortConnectionTest(*connection[:2]):
                        self._id = sessionid
                        ip, port, timestamp = connection
                        args = list(connection[:-1]) + list(self._args)
                        client = self._clientclass(*args, **self._kwargs)
                        client.connect(sessionid)
                        self._connection = connection
                        self._client = client
                        return
                except Exception as e:
                    print(("Error occured %s" % e))
                    pass # invalidate the client
                if self._client:
                    self._client.close()
                connection[2] = time.time()
        ips = [ "%s:%s" % (con[0], con[1]) for con in self._connections ]
        msg = "Failed to connect to %s" % (", ".join(ips))
        raise j.exceptions.OPERATIONS(msg)

    @retry
    def sendMsg(self, category, cmd, data, sendformat="", returnformat="",timeout=None):
        pass

    def close(self):
        if self._client:
            self._client.close()

    def __str__(self):
        return "%s %s" % (self.__class__.__name__, self._connections)
