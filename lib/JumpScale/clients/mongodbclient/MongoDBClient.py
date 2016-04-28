from JumpScale import j

from pymongo import MongoClient, MongoReplicaSetClient

class MongoDBClient:
    def __init__(self):
        self.__jslocation__ = "j.clients.mongodb"

    def get(self, host='localhost', port=27017, ssl=False):
        """
        host can be 
            mongodb://[username:password@]host1[:port1][,host2[:port2],...[,hostN[:portN]]][/[database][?options]]
        """
        try:
            client = MongoClient(host, int(port))
        except Exception as e:
            raise j.exceptions.RuntimeError('Could not connect to mongodb server on %s:%s\nerror:%s' % (host, port,e))
        else:
            return client

    def getByInstance(self, instancename):
        hrd = j.application.getAppInstanceHRD(name="mongodb_client",instance=instancename)
        if hrd is None:
            raise j.exceptions.OPERATIONS("Could not find mongodb_client for instance %s" % instancename)
        ipaddr = hrd.get("param.addr")
        port = hrd.getInt("param.port")    
        ssl = False
        if hrd.exists('param.ssl'):
            ssl = hrd.getBool('param.ssl')
        replicaset = ""
        if hrd.exists('param.replicaset'):
            replicaset = hrd.get('param.replicaset')
        if replicaset == "":
            return MongoClient(host=ipaddr, port=port, ssl=ssl)
        else:
            return MongoReplicaSetClient(ipaddr, port=port, ssl=ssl, replicaSet=replicaset)
