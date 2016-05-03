from JumpScale import j
from servers.gridhealthchecker.gridhealthchecker import GridHealthChecker


# class ZCoreModelsFactory():

#     def getModelObject(self, ddict={}):
#         return ModelObject(ddict)


class GridFactory():

    def __init__(self):
        self.__jslocation__ = "j.core.grid"
        self.brokerClient = None
        # self.zobjects = ZCoreModelsFactory()
        self.id = None
        self.nid=None
        self.config = None
        self.roles = list()
        self._healthchecker = None
    
    @property
    def healthchecker(self):
        if not self._healthchecker:
            self._healthchecker = GridHealthChecker()
        return self._healthchecker

    def _loadConfig(self,test=True):
        if "config" not in j.application.__dict__:
            raise RuntimeWarning("Grid/Broker is not configured please run configureBroker/configureNode first and restart jshell")
        self.config = j.application.config

        if self.config == None:
            raise RuntimeWarning("Grid/Broker is not configured please run configureBroker/configureNode first and restart jshell")

        self.id = j.application.whoAmI.gid
        self.nid = j.application.whoAmI.nid

        if test:

            if self.id == 0:
                raise j.exceptions.Input("Grid needs grid id to be filled in in grid config file")

            if self.nid == 0:
                raise j.exceptions.Input("Grid needs grid node id (grid.nid) to be filled in in grid config file")


    def init(self,description="",instance=1):
        self._loadConfig(test=False)

        roles = list()
        if self.config.exists("grid.node.roles"):
            roles = j.application.config.getList('grid.node.roles')
        roles = [ role.lower() for role in roles ]
        self.roles = roles
        j.logger.consoleloglevel = 5

    def getLocalIPAccessibleByGridMaster(self):
        return j.sal.nettools.getReachableIpAddress(self.config.get("grid.master.ip"), 5544)

    def isGridMasterLocal(self):
        broker = self.config.get("grid.master.ip")
        return j.sal.nettools.isIpLocal(broker)
