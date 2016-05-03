from JumpScale import j
import zmq
from servers.serverbase.DaemonClient import Transport
from servers.serverbase.TCPHATransport import TCPHATransport


class ZDaemonTransport(Transport):
    def __init__(self, addr="localhost", port=9999,gevent=False):

        self._timeout = 60
        self._addr = addr
        self._port = port
        self._id = None
        if gevent==False:
            import zmq
            import threading
            self.zmq=zmq
            self._lock = threading.RLock()
        else:
            import zmq.green as zmq
            import gevent.coros
            self.zmq=zmq
            self._lock = gevent.coros.RLock()
        

    def connect(self, sessionid):
        """
        everwrite this method in implementation to init your connection to server (the transport layer)
        """
        self._id = sessionid
        self._init()

    def sendMsg(self, category, cmd, data, sendformat="", returnformat="",timeout=None):
        """
        overwrite this class in implementation to send & retrieve info from the server (implement the transport layer)

        @return (resultcode,returnformat,result)
                item 0=cmd, item 1=returnformat (str), item 2=args (dict)
        resultcode
            0=ok
            1= not authenticated
            2= method not found
            2+ any other error

        @param timeout is not used
        """
        with self._lock:
            self._cmdchannel.send_multipart([category, cmd, sendformat, returnformat, data])
            result=self._cmdchannel.recv_multipart()
        return result

    def _init(self):
        j.logger.log("check server is reachable on %s on port %s" % (self._addr, self._port), level=4, category='zdaemon.client.init')
        res = j.sal.nettools.waitConnectionTest(self._addr, self._port, 10)

        if res == False:
            msg = "Could not find a running server instance on %s:%s" % (self._addr, self._port)
            raise j.exceptions.OPERATIONS(msg)
        j.logger.log("server is reachable on %s on port %s" % (self._addr, self._port), level=4, category='zdaemon.client.init')

        self._context = self.zmq.Context()

        self._cmdchannel = self._context.socket(self.zmq.REQ)

        self._cmdchannel.setsockopt(self.zmq.IDENTITY, str(self._id))

        # if self.port == 4444 and j.core.platformtype.myplatform.isLinux():
        #     self.cmdchannel.connect("ipc:///tmp/cmdchannel_clientdaemon")
        #     print "IPC channel opened to client daemon"
        # else:
        self._cmdchannel.connect("tcp://%s:%s" % (self._addr, self._port))
        print(("TCP channel open to %s:%s with id:%s" % (self._addr, self._port,self._id)))

        self._poll = self.zmq.Poller()
        self._poll.register(self._cmdchannel, self.zmq.POLLIN)
        print("TCP channel OK")

    def close(self):
        try:
            self._cmdchannel.setsockopt(self.zmq.LINGER, 0)
            self._cmdchannel.close()
        except:
            print("error in close for cmdchannel")
            pass

        try:
            self._poll.unregister(self._cmdchannel)
        except:
            pass

        self._context.term()

class ZDaemonHATransport(TCPHATransport):
    def __init__(self, connections, gevent=False):
        TCPHATransport.__init__(self, connections, ZDaemonTransport, gevent)
