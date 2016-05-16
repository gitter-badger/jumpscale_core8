#!/usr/bin/env python
from JumpScale import j


from sal.base.SALObject import SALObject

class Container(SALObject):
    """Docker Container"""

    def __init__(self, name, id, client, host="localhost"):

        self.client = client

        self.host = host
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
            self._executor = j.tools.executor.getSSHBased(addr=self.host, port=self.ssh_port, login='root', passwd="gig1234")
            self._executor.sshclient.connectTest(timeout=10)
        return self._executor

    @property
    def cuisine(self):
        if self._cuisine is None:
            self._cuisine = j.tools.cuisine.get(self.executor)
        return self._cuisine

    def run(self, name, cmd):
        cmd2 = "docker exec -i -t %s %s" % (self.name, cmd)
        j.sal.process.executeWithoutPipe(cmd2)

    def execute(self, path):
        """
        execute file in docker
        """
        self.copy(path, path)
        self.run("chmod 770 %s;%s" % (path, path))

    def copy(self, src, dest):
        rndd = j.data.idgenerator.generateRandomInt(10, 1000000)
        temp = "/var/docker/%s/%s" % (self.name, rndd)
        j.sal.fs.createDir(temp)
        source_name = j.sal.fs.getBaseName(src)
        if j.sal.fs.isDir(src):
            j.sal.fs.copyDirTree(src, j.sal.fs.joinPaths(temp, source_name))
        else:
            j.sal.fs.copyFile(src, j.sal.fs.joinPaths(temp, source_name))

        ddir = j.sal.fs.getDirName(dest)
        cmd = "mkdir -p %s" % (ddir)
        self.run(name, cmd)

        cmd = "cp -r /var/jumpscale/%s/%s %s" % (rndd, source_name, dest)
        self.run(self.name, cmd)
        j.sal.fs.remove(temp)


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
        raise j.exceptions.RuntimeError("not implemented")
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
        raise j.exceptions.RuntimeError("not implemented")
        # print("Install jumpscale8")
        # # c = self.getSSH(name)
        #
        # c.fabric.state.output["running"] = True
        # c.fabric.state.output["stdout"] = True
        # c.fabric.api.env['shell_env'] = {"JSBRANCH": branch, "AYSBRANCH": branch}
        # c.run("cd /tmp;rm -f install.sh;curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/master/install/install.sh > install.sh;bash install.sh")
        # c.run("cd /opt/code/github/jumpscale/jumpscale_core8;git remote set-url origin git@github.com:Jumpscale/jumpscale_core8.git")
        # c.run("cd /opt/code/github/jumpscale/ays_jumpscale8;git remote set-url origin git@github.com:Jumpscale/ays_jumpscale8.git")
        # c.fabric.state.output["running"] = False
        # c.fabric.state.output["stdout"] = False
        #
        # C = """
        # Host *
        #     StrictHostKeyChecking no
        # """
        # c.file_write("/root/.ssh/config", C)
        # if not j.sal.fs.exists(path="/root/.ssh/config"):
        #     j.sal.fs.writeFile("/root/.ssh/config", C)
        # C2 = """
        # apt-get install language-pack-en
        # # apt-get install make
        # locale-gen
        # echo "installation done" > /tmp/ok
        # """
        # ssh_port = self.getPubPortForInternalPort(name, 22)
        # j.do.executeBashScript(content=C2, remote="localhost", sshport=ssh_port)

    def setHostName(self, hostname):
        self.cuisine.core.sudo("echo '%s' > /etc/hostname" % hostname)
        self.cuisine.core.sudo("echo %s >> /etc/hosts" % hostname)

    def getPubPortForInternalPort(self, port):

        for key,portsDict in self.info["NetworkSettings"]["Ports"].items():
            if key.startswith(str(port)):
                # if "PublicPort" not in port2:
                #     raise j.exceptions.Input("cannot find publicport for ssh?")
                portsfound=[int(item['HostPort']) for item in portsDict]
                if len(portsfound)>0:
                    return portsfound[0]

        raise j.exceptions.Input("cannot find publicport for ssh?")

    def pushSSHKey(self, keyname="", sshpubkey="", local=True):
        keys = set()
        if local:
            dir = j.tools.path.get('/root/.ssh')
            for file in dir.listdir("*.pub"):
                keys.add(file.text())

        if sshpubkey and j.data.types.string.check(sshpubkey):
            keys.add(sshpubkey)

        if keyname is not None and keyname != '':
            if not j.do.checkSSHAgentAvailable:
                j.do.loadSSHAgent()

            key = j.do.getSSHKeyFromAgentPub(keyname)
            if key:
                keys.add(key)

        j.sal.fs.writeFile(filename="/root/.ssh/known_hosts", contents="")
        for key in keys:
            self.cuisine.ssh.authorize("root", key)

        return list(keys)

    def cleanAysfs(self):
        # clean default /optvar aysfs if any
        aysfs = j.sal.aysfs.get('%s-optvar' % self.name, None)

        # if load config return True, config exists
        if aysfs.loadConfig():
            # stopping any running aysfs linked
            if aysfs.isRunning():
                aysfs.stop()
                print("[+] aysfs stopped")

    def destroy(self):
        self.cleanAysfs()

        try:
            self.client.kill(self.id)
        except Exception as e:
            print ("could not kill:%s"%self.id)
        try:
            self.client.remove_container(self.id)
        except Exception as e:
            print ("could not kill:%s"%self.id)

    def stop(self):
        self.cleanAysfs()
        self.client.kill(self.id)

    def restart(self):
        self.client.restart(self.id)

    def commit(self, imagename, msg="", delete=True, force=False):
        """
        imagename: name of the image to commit. e.g: jumpscale/myimage
        delete: bool, delete current image before doing commit
        force: bool, force delete
        """
        if delete:
            res = j.sal.docker.client.images(imagename)
            if len(res) > 0:
                self.client.remove_image(imagename, force=force)
        self.client.commit(self.id, imagename, message=msg)

    def uploadFile(self, source, dest):
        """
        put a file located at source on the host to dest into the container
        """
        self.copy(self.name, source, dest)

    def downloadFile(self, source, dest):
        """
        get a file located at source in the host to dest on the host

        """
        if not self.cuisine.core.file_exists(source):
            raise j.exceptions.Input(msg="%s not found in container" % source)
        ddir = j.sal.fs.getDirName(dest)
        j.sal.fs.createDir(ddir)
        content = self.cuisine.core.file_read(source)
        j.sal.fs.writeFile(dest, content)


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
    #     # if j.sal.fs.exists(path=hrdf):
    #     #     c.dir_ensure("/opt/jumpscale8/hrd/system",True)
    #     #     c.file_upload(hrdf,hrdf)
    #     # c.fabric.state.output["running"]=True
    #     # c.fabric.state.output["stdout"]=True
    #     # c.run("cd /opt/code/github/jumpscale/jumpscale_core8/install/ && bash install.sh")
    #     c=self.getSSH(name)
    #
    #     c.fabric.state.output["running"]=True
    #     c.fabric.state.output["stdout"]=True
    #     c.fabric.api.env['shell_env']={"JSBRANCH":branch,"AYSBRANCH":branch}
    #     c.run("cd /tmp;rm -f install.sh;curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/master/install/install.sh > install.sh;bash install.sh")
    #     c.run("cd /opt/code/github/jumpscale/jumpscale_core8;git remote set-url origin git@github.com:Jumpscale/jumpscale_core8.git")
    #     c.run("cd /opt/code/github/jumpscale/ays_jumpscale8;git remote set-url origin git@github.com:Jumpscale/ays_jumpscale8.git")
    #     c.fabric.state.output["running"]=False
    #     c.fabric.state.output["stdout"]=False
    #
    #     C="""
    #     Host *
    #         StrictHostKeyChecking no
    #     """
    #     c.file_write("/root/.ssh/config",C)
    #     if not j.sal.fs.exists(path="/root/.ssh/config"):
    #         j.sal.fs.writeFile("/root/.ssh/config",C)
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
    #     raise j.exceptions.RuntimeError("not implemented")
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
    #     raise j.exceptions.RuntimeError("not implemented")
    #     if not self.btrfsSubvolExists(name):
    #         cmd="subvolume create %s/%s"%(self.basepath,name)
    #         self._btrfsExecute(cmd)

    # def btrfsSubvolCopy(self,nameFrom,NameDest):
    #     raise j.exceptions.RuntimeError("not implemented")
    #     if not self.btrfsSubvolExists(nameFrom):
    #         raise j.exceptions.RuntimeError("could not find vol for %s"%nameFrom)
    #     if j.sal.fs.exists(path="%s/%s"%(self.basepath,NameDest)):
    #         raise j.exceptions.RuntimeError("path %s exists, cannot copy to existing destination, destroy first."%nameFrom)
    #     cmd="subvolume snapshot %s/%s %s/%s"%(self.basepath,nameFrom,self.basepath,NameDest)
    #     self._btrfsExecute(cmd)

    # def btrfsSubvolExists(self,name):
    #     raise j.exceptions.RuntimeError("not implemented")
    #     subvols=self.btrfsSubvolList()
    #     # print subvols
    #     return name in subvols

    # def btrfsSubvolDelete(self,name):
    #     raise j.exceptions.RuntimeError("not implemented")
    #     if self.btrfsSubvolExists(name):
    #         cmd="subvolume delete %s/%s"%(self.basepath,name)
    #         self._btrfsExecute(cmd)
    #     path="%s/%s"%(self.basepath,name)
    #     if j.sal.fs.exists(path=path):
    #         j.sal.fs.removeDirTree(path)
    #     if self.btrfsSubvolExists(name):
    #         raise j.exceptions.RuntimeError("vol cannot exist:%s"%name)
