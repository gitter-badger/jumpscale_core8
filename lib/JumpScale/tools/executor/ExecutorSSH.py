from JumpScale import j
from ExecutorBase import *
import os

class ExecutorSSH(ExecutorBase):

    def __init__(self, addr, port, dest_prefixes={},login="root",\
            passwd=None,debug=False,checkok=True,allow_agent=True, \
            look_for_keys=True,pushkey=None,pubkey=""):
        ExecutorBase.__init__(self, dest_prefixes=dest_prefixes,debug=debug,checkok=checkok)
        self.logger = j.logger.get("j.tools.executor.ssh")
        self.id = '%s:%s:%s' % (addr, port, login)
        self.addr = addr
        self._port = int(port)
        self._login=login
        self._passwd=passwd
        if passwd!=None:
            look_for_keys=False
            allow_agent=False
        self.allow_agent=allow_agent
        self.look_for_keys=look_for_keys
        self.pushkey=pushkey
        self.pubkey=pubkey
        self._sshclient=None
        self.type="ssh"
        if checkok:
            self.sshclient.connectTest()

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self,val):
        self._login=val
        self._sshclient=None

    @property
    def passwd(self):
        return self._passwd

    @passwd.setter
    def passwd(self,passwd):
        if passwd!=None:
            self.look_for_keys=False
            self.allow_agent=False
        self._passwd=passwd
        self._sshclient=None

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self,val):
        self._port=int(val)
        self._sshclient=None

    @property
    def sshclient(self):
        if self._sshclient==None:
            self._sshclient=j.clients.ssh.get(self.addr,self.port,login=self.login,passwd=self.passwd,allow_agent=self.allow_agent, look_for_keys=self.look_for_keys)
            if self.pushkey is not None:
                #lets push the ssh key as specified
                if j.sal.fs.exists(self.pushkey):
                    path=self.pushkey
                else:
                    homedir=os.environ["HOME"]
                    path="%s/.ssh/%s.pub"%(homedir,self.pushkey)
                if self.pubkey=="":
                    pubkey=self.pubkey
                if j.sal.fs.exists(path):
                    pubkey=j.sal.fs.fileGetContents(path)
                else:
                    raise j.exceptions.RuntimeError("Could not find key:%s"%path)

                self._sshclient.ssh_authorize("root",pubkey)

        return self._sshclient

    def execute(self, cmds, die=True,checkok=None, async=False, showout=True, combinestdr=True,timeout=0, env={}):
        """
        @param naked means will not manipulate cmd's to show output in different way
        @param async is not used method, but is only used for interface comaptibility
        return (rc,out,err)
        """
        if env:
            self.env.update(env)
        self.logger.info("cmd: %s" % cmds)
        cmds2=self._transformCmds(cmds,die,checkok=checkok)


        if cmds.find("\n") != -1:
            if showout:
                self.logger.info("EXECUTESCRIPT} %s:%s:\n%s"%(self.addr,self.port,cmds))
            else:
                self.logger.debug("EXECUTESCRIPT} %s:%s:\n%s"%(self.addr,self.port,cmds))
            retcode,out=j.do.executeBashScript(content=cmds2,path=None,die=die,remote=self.addr,sshport=self.port)
        else:
            # online command, we use cuisine
            if showout:
                self.logger.info("EXECUTE %s:%s: %s"%(self.addr,self.port,cmds))
            else:
                self.logger.debug("EXECUTE %s:%s: %s"%(self.addr,self.port,cmds))
            retcode,out=self.sshclient.execute(cmds2,die=die,showout=showout, combinestdr=combinestdr)

        if checkok and die:
            self.docheckok(cmds,out)

        return (retcode,out)


    def upload(self, source, dest, dest_prefix="",recursive=True, createdir=True):

        if dest_prefix != "":
            dest = j.sal.fs.joinPaths(dest_prefix,dest)
        if dest[0] !="/":
            raise j.exceptions.RuntimeError("need / in beginning of dest path")
        dest = "root@%s:%s" % (self.addr, dest)
        j.sal.fs.copyDirTree(source, dest, keepsymlinks=True, deletefirst=False, \
            overwriteFiles=True, ignoredir=[".egg-info", ".dist-info"], ignorefiles=[".egg-info"], rsync=True,\
            ssh=True, sshport=self.port,recursive=recursive, createdir=createdir)


    def download(self, source, dest, source_prefix="",recursive=True):
        if source_prefix != "":
            source = j.sal.fs.joinPaths(source_prefix,source)
        if source[0] !="/":
            raise j.exceptions.RuntimeError("need / in beginning of source path")
        source = "root@%s:%s" % (self.addr,source)
        j.sal.fs.copyDirTree(source, dest, keepsymlinks=True, deletefirst=False, \
            overwriteFiles=True, ignoredir=[".egg-info",".dist-info"], ignorefiles=[".egg-info"], rsync=True,\
            ssh=True, sshport=self.port,recursive=recursive)
