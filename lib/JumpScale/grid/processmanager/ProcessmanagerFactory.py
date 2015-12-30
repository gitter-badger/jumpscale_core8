from JumpScale import j
import JumpScale.grid.osis
# import JumpScale.baselib.stataggregator
import JumpScale.grid.jumpscripts
import sys
import psutil
import importlib
import time
import JumpScale.baselib.redis2

class Dummy():
    pass

class DummyDaemon():
    def __init__(self):
        self.cmdsInterfaces={}
        self._osis = None

    def _adminAuth(self,user,passwd):
        raise RuntimeError("permission denied")

    @property
    def osis(self):
        if not self._osis:
            try:
                self._osis = j.clients.osis.getByInstance()
            except KeyError:
                return None
        return self._osis

    def addCMDsInterface(self, cmdInterfaceClass, category):
        if category not in self.cmdsInterfaces:
            self.cmdsInterfaces[category] = []
        self.cmdsInterfaces[category].append(cmdInterfaceClass())

class ProcessmanagerFactory:

    """
    """
    def __init__(self):
        self.__jslocation__ = "j.core.processmanager"
        self.daemon = DummyDaemon()
        self.basedir = j.sal.fs.joinPaths(j.dirs.base, 'apps', 'processmanager')
        j.system.platform.psutil = psutil

        if "processmanager" in j.__dict__ and "redis_queues" in j.processmanager.__dict__:
            self.redis=j.processmanager.redis_mem
        else:
            self.redis = j.clients.redis.getByInstance("system")

    def start(self):

        j.core.jumpscripts.loadFromAC()

        osis = self.daemon.osis
        self.daemon = j.servers.geventws.getServer(port=4446)  #@todo no longer needed I think, it should not longer be a socket server, lets check first
        self.daemon.osis = osis
        self.daemon.daemon.osis = osis

        #clean old stuff from redis
        import JumpScale.baselib.redis2worker
        j.clients.redisworker.deleteProcessQueue()
        # j.clients.redisworker.deleteJumpscripts() #CANNOT DO NOW BECAUSE ARE STILL RELYING ON ID's so could be someone still wants to execute

        self.redis.set("processmanager:startuptime",str(int(time.time())))

        self.starttime=j.data.time.getTimeEpoch()

        self.loadCmds()

        self.cmds.jumpscripts.schedule()
                
        self.daemon.start()

    def _checkIsNFSMounted(self,check=""):
        if check=="":
            check=j.dirs.codeDir
        rc,out=j.sal.process.execute("mount")
        found=False
        for line in out.split("\n"):
            if line.find(check)!=-1:
                found=True
        return found

    def restartWorkers(self):
        for queuename in ('default', 'io', 'hypervisor', 'process'):
            j.clients.redisworker.redis.lpush("workers:action:%s"%queuename,"RESTART")

    def getCmdsObject(self,category):
        if category in self.cmds:
            return self.cmds["category"]
        else:
            raise RuntimeError("Could not find cmds with category:%s"%category)

    def loadCmds(self):
        if self.basedir not in sys.path:
            sys.path.insert(0, self.basedir)
        cmds=j.sal.fs.listFilesInDir(j.sal.fs.joinPaths(self.basedir,"processmanagercmds"),filter="*.py")
        cmds.sort()
        for item in cmds:
            name=j.sal.fs.getBaseName(item).replace(".py","")
            if name[0]!="_":
                module = importlib.import_module('processmanagercmds.%s' % name)
                classs = getattr(module, name)
                print("load cmds object:%s"%name)
                tmp=classs(daemon=self.daemon)
                self.daemon.addCMDsInterface(classs, category=tmp._name)

        self.cmds=Dummy()
        if self.daemon.osis:
            self.loadMonitorObjectTypes()

        def sort(item):
            key,cmd=item
            return getattr(cmd, 'ORDER', 10000)        

        for key, cmd in sorted(iter(self.daemon.daemon.cmdsInterfaces.items()), key=sort):

            self.cmds.__dict__[key]=cmd
            if hasattr(self.cmds.__dict__[key],"_init"):
                print("### INIT ###:%s"%key)
                self.cmds.__dict__[key]._init()

    def loadMonitorObjectTypes(self):
        if self.basedir not in sys.path:
            sys.path.insert(0, self.basedir)
        self.monObjects=Dummy()
        for item in j.sal.fs.listFilesInDir(j.sal.fs.joinPaths(self.basedir,"monitoringobjects"),filter="*.py"):
            name=j.sal.fs.getBaseName(item).replace(".py","")
            if name[0]!="_":
                monmodule = importlib.import_module('monitoringobjects.%s' % name)
                classs=getattr(monmodule, name)
                print("load monitoring object:%s"%name)
                factory = getattr(monmodule, '%sFactory' % name)(self, classs)
                self.monObjects.__dict__[name.lower()]=factory   

    def getStartupTime(self):
        val=self.redis.get("processmanager:startuptime")
        return int(val)

    def checkStartupOlderThan(self,secago):
        return self.getStartupTime()<int(time.time())-secago

