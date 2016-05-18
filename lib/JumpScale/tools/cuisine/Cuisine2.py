
from JumpScale import j



from CuisineInstaller import CuisineInstaller
from CuisineInstallerDevelop import CuisineInstallerDevelop
from CuisinePackage import CuisinePackage
from CuisineProcess import CuisineProcess
from CuisinePIP import CuisinePIP
from CuisineNet import CuisineNet
from CuisineSSH import CuisineSSH
from CuisineNS import CuisineNS
from CuisineUser import CuisineUser
from CuisineGit import CuisineGit
from apps.CuisineApps import CuisineApps
from CuisineBuilder import CuisineBuilder
from CuisineGroup import CuisineGroup
from CuisineGolang import CuisineGolang
from CuisineFW import CuisineFW
from CuisineDocker import CuisineDocker
from ProcessManagerFactory import ProcessManagerFactory
from CuisineSSHReflector import CuisineSSHReflector
from CuisineProxy import CuisineProxy
from CuisineBootMediaInstaller import CuisineBootMediaInstaller
from CuisineVRouter import CuisineVRouter
from CuisineTmux import CuisineTmux
from CuisineGeoDns import CuisineGeoDns
from CuisineCore import CuisineCore
from CuisinePNode import CuisinePNode
from CuisineStor import CuisineStor

class JSCuisine:

    def __init__(self,executor):

        self.executor = executor
        self.runid = self.id

        self._installer = None
        self._platformtype=None
        self._id=None
        self._package=None
        self._processmanager=None
        self._installerdevelop=None
        self._process=None
        self._pip=None
        self._ns=None
        self._ssh=None
        self._net=None
        self._group=None
        self._user=None
        self._git=None
        self._apps=None
        self._bash=None
        self._avahi=None
        self._tmux=None
        self._golang=None
        self._fw=None
        self.cuisine=self
        self._fqn=""
        self._dnsmasq=None
        self._docker=None
        self._js8sb=None
        self._geodns=None
        self._builder=None

        self.core=CuisineCore(self.executor,self)

        self.sshreflector=CuisineSSHReflector(self.executor,self)
        self.proxy=CuisineProxy(self.executor,self)
        self.bootmediaInstaller=CuisineBootMediaInstaller(self.executor,self)
        self.vrouter=CuisineVRouter(self.executor,self)
        self.tmux=CuisineTmux(self.executor,self)

        self.pnode=CuisinePNode(self.executor,self)

        self.stor = CuisineStor(self.executor,self)




        self.done=[]

    @property
    def btrfs(self):
        j.sal.btrfs._executor=self.executor
        return j.sal.btrfs

    @property
    def package(self):
        if self._package==None:
            self._package=CuisinePackage(self.executor,self)
        return self._package

    @property
    def process(self):
        if self._process==None:
            self._process=CuisineProcess(self.executor,self)
        return self._process

    @property
    def pip(self):
        if self._pip==None:
            self._pip=CuisinePIP(self.executor,self)
        return self._pip

    @property
    def fw(self):
        if self._fw==None:
            self._fw=CuisineFW(self.executor,self)
        return self._fw

    @property
    def golang(self):
        if self._golang==None:
            self._golang=CuisineGolang(self.executor,self)
        return self._golang
    @property
    def geodns(self):
        if self._geodns==None:
            self._geodns = CuisineGeoDns(self.executor, self)
        return self._geodns

    @property
    def apps(self):
        if self._apps==None:
            self._apps=CuisineApps(self.executor, self)
        return self._apps

    @property
    def builder(self):
        if self._builder==None:
            self._builder=CuisineBuilder(self.executor, self)
        return self._builder

    @property
    def id(self):
        return self.executor.id

    @property
    def platformtype(self):
        if self._platformtype==None:
            self._platformtype=j.core.platformtype.get(self.executor)
        return self._platformtype

    @property
    def installer(self):
        if self._installer==None:
            self._installer=CuisineInstaller(self.executor,self)
        return self._installer

    @property
    def installerdevelop(self):
        if self._installerdevelop==None:
            self._installerdevelop=CuisineInstallerDevelop(self.executor,self)
        return self._installerdevelop

    @property
    def ns(self):
        if self._ns==None:
            self._ns=CuisineNS(self.executor,self)
        return self._ns

    @property
    def docker(self):
        if self._docker==None:
            self._docker=CuisineDocker(self.executor,self)
        return self._docker


    @property
    def ssh(self):
        if self._ssh==None:
            self._ssh=CuisineSSH(self.executor,self)
        return self._ssh

    @property
    def avahi(self):
        if self._avahi==None:
            self._avahi=j.tools.avahi.get(self,self.executor)
        return self._avahi

    @property
    def dnsmasq(self):
        if self._dnsmasq==None:
            self._dnsmasq=j.sal.dnsmasq
            self._dnsmasq.cuisine=self
            self._dnsmasq.executor=self.executor
        return self._dnsmasq

    @property
    def bash(self):
        if self._bash==None:
            self._bash=j.tools.bash.get(self,self.executor)
        return self._bash

    @property
    def net(self):
        if self._net==None:
            self._net=CuisineNet(self.executor,self)
        return self._net


    @property
    def user(self):
        if self._user==None:
            self._user=CuisineUser(self.executor,self)
        return self._user

    @property
    def group(self):
        if self._group==None:
            self._group=CuisineGroup(self.executor,self)
        return self._group

    @property
    def git(self):
        if self._git==None:
            self._git=CuisineGit(self.executor,self)
        return self._git


    @property
    def processmanager(self):
        if self._processmanager==None:
            self._processmanager = ProcessManagerFactory(self).get()
        return self._processmanager


    def __str__(self):
        return "cuisine:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))

    __repr__=__str__
