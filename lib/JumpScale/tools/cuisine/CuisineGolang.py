
from JumpScale import j
# import os

# import socket

from ActionDecorator import ActionDecorator
class actionrun(ActionDecorator):
    def __init__(self,*args,**kwargs):
        ActionDecorator.__init__(self,*args,**kwargs)
        self.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.golang"



class CuisineGolang():

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine

    @actionrun(action=True)
    def install(self):
        self.cuisine.installer.base()
        rc, out = self.cuisine.core.run("which go", die=False,showout=False,action=True)
        if rc > 0:
            if self.cuisine.core.isMac or self.cuisine.core.isArch:
                self.cuisine.package.install("go")
            elif "ubuntu" in self.cuisine.platformtype.platformtypes:
                # self.cuisine.core.run("apt-get install golang -y --force-yes")
                downl = "https://storage.googleapis.com/golang/go1.6.linux-amd64.tar.gz"
                self.cuisine.core.file_download(downl,"/usr/local",overwrite=False,retry=3,timeout=0,expand=True)
            else:
                raise j.exceptions.RuntimeError("platform not supported")


        optdir = self.cuisine.core.dir_paths["optDir"]
        goDir = self.cuisine.core.dir_paths['goDir']
        self.cuisine.bash.environSet("GOPATH", goDir)
        self.cuisine.bash.environSet("GOROOT", '/usr/local/go')

        self.cuisine.bash.addPath(self.cuisine.core.joinpaths(goDir, 'bin'))
        self.cuisine.bash.addPath("/usr/local/go/bin/")

        self.cuisine.core.dir_ensure("%s/src" % goDir)
        self.cuisine.core.dir_ensure("%s/pkg" % goDir)
        self.cuisine.core.dir_ensure("%s/bin" % goDir)

        self.get("github.com/tools/godep")
        # self.get("github.com/rcrowley/go-metrics")

    @property
    def GOPATH(self):
        return self.cuisine.core.dir_paths["goDir"]
        # if self._gopath==None:
        #     # if not "GOPATH" in self.bash.environ:
        #     #     self.cuisine.installerdevelop.golang()
        #     # self._gopath=   self.bash.environ["GOPATH"]

        # return self._gopath


    @actionrun(action=True)
    def get(self,url):
        """
        e.g. url=github.com/tools/godep
        """
        self.cuisine.core.run('go get -v -u %s'%url, profile=True)

    @actionrun(action=True)
    def godep(self, url, branch=None, depth=1):
        """
        e.g. url=github.com/tools/godep
        """
        GOPATH = self.cuisine.bash.environ['GOPATH']

        pullurl = "git@%s.git" % url.replace('/', ':', 1)

        dest = self.cuisine.git.pullRepo(pullurl, branch=branch, depth=depth, dest='%s/src/%s' % (GOPATH, url), ssh=False)
        self.cuisine.core.run('cd %s && godep restore' % dest, profile=True)
