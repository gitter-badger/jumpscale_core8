from JumpScale import j
# import JumpScale.grid
# import zmq
import gevent
import gevent.monkey
# monkey.patch_thread()
gevent.monkey.patch_time()
import zmq.green as zmq

GeventLoop = j.core.gevent.getGeventLoopClass()


class ZDaemon(GeventLoop):

    def __init__(self, port=None, name="", nrCmdGreenlets=50, sslorg="", ssluser="", sslkeyvaluestor=None):
        gevent.monkey.patch_socket()
        GeventLoop.__init__(self)
        self.name = name
        self.logger = j.logger.get(name)

        if sslkeyvaluestor == None:
            sslkeyvaluestor = j.sal.ssl.getSSLHandler(sslkeyvaluestor)

        self.daemon = j.servers.base.getDaemon(name="unknown", sslorg="", ssluser="", sslkeyvaluestor=None)

        # self.ports = [] #is for datachannel
        # self.sockets = {} #is for datachannel
        # self.watchdog = {}  # active ports are in this list

        self.port = port

        if port==None:
            raise j.exceptions.RuntimeError("Port cannot be none")

        self.nrCmdGreenlets = nrCmdGreenlets

        self.key = ""

    def addCMDsInterface(self, cmdInterfaceClass, category=""):
        self.daemon.addCMDsInterface(cmdInterfaceClass, category)

    def repCmdServer(self):
        cmdsocket = self.cmdcontext.socket(zmq.REP)
        cmdsocket.connect("inproc://cmdworkers")
        while True:
            category, cmd, informat, returnformat, data, sessionid = cmdsocket.recv_multipart()
            # print "startrpc"
            result = self.daemon.processRPCUnSerialized(cmd, informat, returnformat, data, sessionid, category)
            # print "stoprpc"
            cmdsocket.send_multipart(result)
            # print 'senddonerpc'

    def cmdGreenlet(self):
        # Nonblocking, e.g the osis server contains a broker which queus internally the messages.
        self.cmdcontext = zmq.Context()

        frontend = self.cmdcontext.socket(zmq.ROUTER)
        backend = self.cmdcontext.socket(zmq.DEALER)

        frontend.bind("tcp://*:%s" % self.port)
        backend.bind("inproc://cmdworkers")

        # Initialize poll set
        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)

        workers = []

        for i in range(self.nrCmdGreenlets):
            workers.append(gevent.spawn(self.repCmdServer))

        j.logger.log("init cmd channel on port:%s for daemon:%s" % (self.port, self.name), level=5, category="zdaemon.init")

        while True:
            socks = dict(poller.poll())
            if socks.get(frontend) == zmq.POLLIN:
                parts = frontend.recv_multipart()
                parts.append(parts[0])  # add session id at end
                backend.send_multipart([parts[0]] + parts)

            if socks.get(backend) == zmq.POLLIN:
                parts = backend.recv_multipart()
                frontend.send_multipart(parts[1:])  # @todo dont understand why I need to remove first part of parts?

    def start(self, mainloop=None):
        print(("starting %s"%self.name))
        self.schedule("cmdGreenlet", self.cmdGreenlet)
        self.startClock()

        print(("start %s on port:%s"%(self.name,self.port)))
        if mainloop != None:
            mainloop()
        else:
            while True:
                gevent.sleep(100)

    # UNFINISHED CODE FOR DATACHANNEL (still duplicate code inside) ################################

    # def datachannelStart(self):
    #     self.schedule("returok", self.datachannelReturnok)
    #     self.schedule("watchdog",self.watchdogCheck)
    #     self.schedule("watchdogReset",self.watchdogReset)


    # def datachannelProcessor(self, port):
    #     context = zmq.Context()
    #     socket = context.socket(zmq.PAIR)

    #     socket.bind("tcp://*:%s" % port)
    #     self.sockets[port] = socket

    #     self.ports.append(port)

    #     print "init data port:%s"%port
    #     while True:
    #         msg = socket.recv()
    #         self.watchdog[port] = True
    #         if msg == "WATCHDOG":
    #             continue
    #         self.processRPC(msg)

    # def datachannelReturnok(self):
    #     """
    #     will every 5 sec go back to sender to acknowledge succesfull processed items
    #     """
    #     while True:
    #         self.socket.send(str(self.counter))
    # print "send"
    #         gevent.sleep(5)

    # def getfreeportAndSchedule(self, name, method, **args):
    #     """
    #     find a free port & attach method to it

    #     """
    #     found = None
    #     for i in range(5010, 5300):
    #         if i not in self.ports:
    #             found = i
    #             break
    #     if found == None:
    #         raise j.exceptions.RuntimeError("Could not find free port")

    #     self.schedule("port_%s"%found, method, port=found, **args)

    #     for i in range(1000):
    #         if found in self.ports:
    #             return found
    #         gevent.sleep(0.01)

    #     self.logger.warn_tb(j.exceptions.OPERATIONS, "Cannot open port nr %s for client daemon."%found)
    #     return 0

    # def watchdogCheck(self):
    # ports without activity are closed
    #     while True:
    #         gevent.sleep(100)
    #         for port in self.ports:
    #             if port not in self.watchdog:
    #                 self.resetPort(port)

    # def resetPort(self, port):
    #     greenlet = self.greenlets["port_%s"%port]
    #     greenlet.kill()
    #     self.sockets[port].setsockopt(zmq.LINGER, 0)
    #     self.sockets[port].close()
    #     print "Killed socket %s"%port
    #     try:
    #         self.watchdog.pop(port)
    #     except:
    #         pass
    #     try:
    #         self.ports.remove(port)
    #     except:
    #         pass

    # def watchdogReset(self):
    #     while True:
    #         gevent.sleep(10)
    # self.watchdog = {}  # reset watchdog table


    #
