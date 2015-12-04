#!/usr/bin/env python
from JumpScale import j
import json

from sal.base.SALObject import SALObject

class Container(SALObject):
    """Docker Container"""

    def __init__(self, name, id, client):

        self.client = client

        self.name = name
        self.id=id

        self._ssh_port = None

        self._sshclient = None
        self._cuisine = None
        self._executor = None

    @property
    def ssh_port(self):
        if self._ssh_port is None:
            self._ssh_port = self.getPubPortForInternalPort( 22)
        return self._ssh_port

    @property
    def sshclient(self):
        if self._sshclient is None:
            self.executor.sshclient.connectTest(timeout=10)
            self._sshclient = self.executor.sshclient
        return self._sshclient

    @property
    def executor(self):
        if self._executor is None:
            self._executor = j.tools.executor.getSSHBased(addr='localhost', port=self.ssh_port, login='root', passwd="gig1234")
            self._executor.sshclient.connectTest(timeout=10)
        return self._executor

    @property
    def cuisine(self):
        if self._cuisine is None:
            self._cuisine = j.tools.cuisine.get(self.executor)
        return self._cuisine

    def run(self, name, cmd):
        cmd2 = "docker exec -i -t %s %s" % (self.name, cmd)
        j.do.executeInteractive(cmd2)

    def execute(self, path):
        """
        execute file in docker
        """
        self.copy(path, path)
        self.run("chmod 770 %s;%s" % (path, path))

    def copy(self, src, dest):
        rndd = j.base.idgenerator.generateRandomInt(10, 1000000)
        temp = "/var/docker/%s/%s" % (self.name, rndd)
        j.system.fs.createDir(temp)
        source_name = j.system.fs.getBaseName(src)
        if j.system.fs.isDir(src):
            j.do.copyTree(src, j.system.fs.joinPaths(temp, source_name))
        else:
            j.do.copyFile(src, j.system.fs.joinPaths(temp, source_name))

        ddir = j.system.fs.getDirName(dest)
        cmd = "mkdir -p %s" % (ddir)
        self.run(name, cmd)

        cmd = "cp -r /var/jumpscale/%s/%s %s" % (rndd, source_name, dest)
        self.run(self.name, cmd)
        j.do.delete(temp)


    @property
    def info(self):
        return self.client.inspect_container(self.id)

    def isRunning(self):
        return self.info["State"]["Running"]==True

    def getIp(self):
        return self.info['NetworkSettings']['IPAddress']

    def getProcessList(self, stdout=True):
        """
        @return [["$name",$pid,$mem,$parent],....,[$mem,$cpu]]
        last one is sum of mem & cpu
        """
        raise RuntimeError("not implemented")
        pid = self.getPid()
        children = list()
        children = self._getChildren(pid, children)
        result = list()
        pre = ""
        mem = 0.0
        cpu = 0.0
        cpu0 = 0.0
        prevparent = ""
        for child in children:
            if child.parent.name != prevparent:
                pre += ".."
                prevparent = child.parent.name
            # cpu0=child.get_cpu_percent()
            mem0 = int(round(child.get_memory_info().rss / 1024, 0))
            mem += mem0
            cpu += cpu0
            if stdout:
                print(("%s%-35s %-5s mem:%-8s" % (pre, child.name, child.pid, mem0)))
            result.append([child.name, child.pid, mem0, child.parent.name])
        cpu = children[0].get_cpu_percent()
        result.append([mem, cpu])
        if stdout:
            print(("TOTAL: mem:%-8s cpu:%-8s" % (mem, cpu)))
        return result

    def installJumpscale(self, branch="master"):
        raise RuntimeError("not implemented")
        # print("Install jumpscale8")
        # # c = self.getSSH(name)
        #
        # c.fabric.state.output["running"] = True
        # c.fabric.state.output["stdout"] = True
        # c.fabric.api.env['shell_env'] = {"JSBRANCH": branch, "AYSBRANCH": branch}
        # c.run("cd /tmp;rm -f install.sh;curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > install.sh;bash install.sh")
        # c.run("cd /opt/code/github/jumpscale/jumpscale_core7;git remote set-url origin git@github.com:Jumpscale/jumpscale_core7.git")
        # c.run("cd /opt/code/github/jumpscale/ays_jumpscale8;git remote set-url origin git@github.com:Jumpscale/ays_jumpscale8.git")
        # c.fabric.state.output["running"] = False
        # c.fabric.state.output["stdout"] = False
        #
        # C = """
        # Host *
        #     StrictHostKeyChecking no
        # """
        # c.file_write("/root/.ssh/config", C)
        # if not j.system.fs.exists(path="/root/.ssh/config"):
        #     j.do.writeFile("/root/.ssh/config", C)
        # C2 = """
        # apt-get install language-pack-en
        # # apt-get install make
        # locale-gen
        # echo "installation done" > /tmp/ok
        # """
        # ssh_port = self.getPubPortForInternalPort(name, 22)
        # j.do.executeBashScript(content=C2, remote="localhost", sshport=ssh_port)

    def setHostName(self, hostname):
        self.cuisine.sudo("echo '%s' > /etc/hostname" % hostname)
        self.cuisine.sudo("echo %s >> /etc/hosts" % hostname)

    def getPubPortForInternalPort(self, port):
        
        for key,portsDict in self.info["NetworkSettings"]["Ports"].items():
            if key.startswith(str(port)):
                # if "PublicPort" not in port2:
                #     j.events.inputerror_critical("cannot find publicport for ssh?")
                portsfound=[int(item['HostPort']) for item in portsDict]
                if len(portsfound)>0:
                    return portsfound[0]

        j.events.inputerror_critical("cannot find publicport for ssh?")
        

    def pushSSHKey(self, keyname="", sshpubkey="", local=True):
        key = None
        if local:
            templates = ['.']
            dir = j.tools.path.get('/root/.ssh')
            for file in dir.listdir("*.pub"):
                key = file.text()
                break

        if sshpubkey is not None and sshpubkey != '':
            key = sshpubkey

        if keyname is not None and keyname != '':
            raise RuntimeError("Not implemented")
            # keypath = j.do.getSSHKeyFromAgent(keyname, die=True)
            # key = j.system.fs.fileGetContents(keypath + ".pub")
            # if key == "":
            #     raise RuntimeError("Could not find key %s in ssh-agent"%keyname)
            # self.cuisine.ssh_authorize("root", key)

        j.system.fs.writeFile(filename="/root/.ssh/known_hosts", contents="")
        self.executor.execute("rm -rf /opt/jumpscale8/hrd/apps/*", showout=False)
        self.executor.execute("git config --global user.email \"ishouldhavebeenchanged@example.com\"", showout=False)

        self.cuisine.ssh_authorize("root", key)

        return key

    def destroy(self):
        self.client.kill(self.id)
        self.client.remove_container(self.id)

    def stop(self):
        self.client.kill(self.id)

    def restart(self):
        self.client.restart(self.id)

    def commit(self, imagename):
        cmd = "docker rmi %s" % imagename
        j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
        cmd = "docker commit %s %s" % (self.name, imagename)
        j.system.process.executeWithoutPipe(cmd)

    def uploadFile(self, source, dest):
        """
        put a file located at source on the host to dest into the container
        """
        self.copy(self.name, source, dest)

    def downloadFile(self, source, dest):
        """
        get a file located at source in the host to dest on the host

        """
        if not self.cuisine.file_exists(source):
            j.events.inputerror_critical(msg="%s not found in container" % source)
        ddir = j.system.fs.getDirName(dest)
        j.system.fs.createDir(ddir)
        content = self.cuisine.file_read(source)
        j.system.fs.writeFile(dest, content)


    def __str__(self):
        return "docker:%s"%self.name

    __repr__=__str__


    # def setHostName(self,name,hostname):
    #     return #@todo
    #     c=self.getSSH(name)
    #     #@todo
    #     # c.run("echo '%s' > /etc/hostname;hostname %s"%(hostname,hostname))
    #

    # def installJumpscale(self,name,branch="master"):
    #     print("Install jumpscale8")
    #     # c=self.getSSH(name)
    #     # hrdf="/opt/jumpscale8/hrd/system/whoami.hrd"
    #     # if j.system.fs.exists(path=hrdf):
    #     #     c.dir_ensure("/opt/jumpscale8/hrd/system",True)
    #     #     c.file_upload(hrdf,hrdf)
    #     # c.fabric.state.output["running"]=True
    #     # c.fabric.state.output["stdout"]=True
    #     # c.run("cd /opt/code/github/jumpscale/jumpscale_core7/install/ && bash install.sh")
    #     c=self.getSSH(name)
    #
    #     c.fabric.state.output["running"]=True
    #     c.fabric.state.output["stdout"]=True
    #     c.fabric.api.env['shell_env']={"JSBRANCH":branch,"AYSBRANCH":branch}
    #     c.run("cd /tmp;rm -f install.sh;curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh > install.sh;bash install.sh")
    #     c.run("cd /opt/code/github/jumpscale/jumpscale_core7;git remote set-url origin git@github.com:Jumpscale/jumpscale_core7.git")
    #     c.run("cd /opt/code/github/jumpscale/ays_jumpscale8;git remote set-url origin git@github.com:Jumpscale/ays_jumpscale8.git")
    #     c.fabric.state.output["running"]=False
    #     c.fabric.state.output["stdout"]=False
    #
    #     C="""
    #     Host *
    #         StrictHostKeyChecking no
    #     """
    #     c.file_write("/root/.ssh/config",C)
    #     if not j.system.fs.exists(path="/root/.ssh/config"):
    #         j.do.writeFile("/root/.ssh/config",C)
    #     C2="""
    #     apt-get install language-pack-en
    #     # apt-get install make
    #     locale-gen
    #     echo "installation done" > /tmp/ok
    #     """
    #     ssh_port=self.getPubPortForInternalPort(name,22)
    #     j.do.executeBashScript(content=C2, remote="localhost", sshport=ssh_port)        


    # def _btrfsExecute(self,cmd):
    #     cmd="btrfs %s"%cmd
    #     print(cmd)
    #     return self._execute(cmd)

    # def btrfsSubvolList(self):
    #     raise RuntimeError("not implemented")
    #     out=self._btrfsExecute("subvolume list %s"%self.basepath)
    #     res=[]
    #     for line in out.split("\n"):
    #         if line.strip()=="":
    #             continue
    #         if line.find("path ")!=-1:
    #             path=line.split("path ")[-1]
    #             path=path.strip("/")
    #             path=path.replace("lxc/","")
    #             res.append(path)
    #     return res

    # def btrfsSubvolNew(self,name):
    #     raise RuntimeError("not implemented")
    #     if not self.btrfsSubvolExists(name):
    #         cmd="subvolume create %s/%s"%(self.basepath,name)
    #         self._btrfsExecute(cmd)

    # def btrfsSubvolCopy(self,nameFrom,NameDest):
    #     raise RuntimeError("not implemented")
    #     if not self.btrfsSubvolExists(nameFrom):
    #         raise RuntimeError("could not find vol for %s"%nameFrom)
    #     if j.system.fs.exists(path="%s/%s"%(self.basepath,NameDest)):
    #         raise RuntimeError("path %s exists, cannot copy to existing destination, destroy first."%nameFrom)
    #     cmd="subvolume snapshot %s/%s %s/%s"%(self.basepath,nameFrom,self.basepath,NameDest)
    #     self._btrfsExecute(cmd)

    # def btrfsSubvolExists(self,name):
    #     raise RuntimeError("not implemented")
    #     subvols=self.btrfsSubvolList()
    #     # print subvols
    #     return name in subvols

    # def btrfsSubvolDelete(self,name):
    #     raise RuntimeError("not implemented")
    #     if self.btrfsSubvolExists(name):
    #         cmd="subvolume delete %s/%s"%(self.basepath,name)
    #         self._btrfsExecute(cmd)
    #     path="%s/%s"%(self.basepath,name)
    #     if j.system.fs.exists(path=path):
    #         j.system.fs.removeDirTree(path)
    #     if self.btrfsSubvolExists(name):
    #         raise RuntimeError("vol cannot exist:%s"%name)

