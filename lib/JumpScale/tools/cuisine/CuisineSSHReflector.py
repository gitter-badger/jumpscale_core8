
from JumpScale import j
import os
import time

import socket

from ActionDecorator import ActionDecorator
class actionrun(ActionDecorator):
    def __init__(self,*args,**kwargs):
        ActionDecorator.__init__(self,*args,**kwargs)
        self.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.sshreflector"


class CuisineSSHReflector:

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine

    @actionrun(action=True)
    def server(self,reset=False,keyname="reflector"):
        """
        configures the server
        to test
        js 'c=j.tools.cuisine.get("stor1:9022");c.installer.sshreflector.server'
        """

        port=9222

        package="dropbear"
        self.cuisine.package.install(package)

        self.cuisine.core.run("rm -f /etc/default/dropbear",die=False)
        self.cuisine.core.run("killall dropbear",die=False   )

        passwd=j.data.idgenerator.generateGUID()
        self.cuisine.user.ensure("sshreflector", passwd=passwd, home="/home/sshreflector", uid=None, gid=None, shell=None, fullname=None, encrypted_passwd=True, group=None)

        self.cuisine.core.run('ufw allow %s'%port,die=False)

        self.cuisine.core.dir_ensure("/home/sshreflector/.ssh", recursive=True, mode=None, owner="sshreflector", group="sshreflector")

        j.application.break_into_jshell("DEBUG NOW reflector")

        lpath=os.environ["HOME"]+"/.ssh/reflector"
        path="/home/sshreflector/.ssh/reflector"
        ftp=self.cuisine.core.executor.sshclient.getSFTP()
        if j.sal.fs.exists(lpath) and j.sal.fs.exists(lpath+".pub"):
            print("UPLOAD EXISTING SSH KEYS")
            ftp.put(lpath,path)
            ftp.put(lpath+".pub",path+".pub")
        else:
            #we do the generation of the keys on the server
            if reset or not self.cuisine.core.file_exists(path) or not self.cuisine.core.file_exists(path+".pub"):
                self.cuisine.core.file_unlink(path)
                self.cuisine.core.file_unlink(path+".pub")
                #-N is passphrase
                self.cuisine.core.run("ssh-keygen -q -t rsa -b 4096 -f %s -N '' "%path)
            ftp.get(path,lpath)
            ftp.get(path+".pub",lpath+".pub")

            j.sal.fs.chmod(lpath,0o600)
            j.sal.fs.chmod(lpath+".pub",0o600)

        #authorize remote server to accept now copied private key
        self.cuisine.ssh.authorize("sshreflector",j.sal.fs.fileGetContents(lpath+".pub"))

        self.cuisine.core.run("chmod 0644 /home/sshreflector/.ssh/*")
        self.cuisine.core.run("chown -R sshreflector:sshreflector /home/sshreflector/.ssh/")

        cpath=self.cuisine.core.run("which dropbear")

        cmd="%s -R -F -E -p 9222 -w -s -g -K 20 -I 60"%cpath
        self.cuisine.processmanager.ensure("reflector", cmd, descr='')

        # self.cuisine.package.start(package)

        self.cuisine.ns.hostfile_set_fromlocal()

        if self.cuisine.process.tcpport_check(port,"dropbear")==False:
            raise j.exceptions.RuntimeError("Could not install dropbear, port %s was not running"%port)


    # @actionrun(action=True)
    def client_delete(self):
        self.cuisine.processmanager.remove("autossh") #make sure leftovers are gone
        self.cuisine.core.run("killall autossh",die=False,showout=False)

    def client(self,remoteids,reset=True):
        """
        chose a port for remote server which we will reflect to
        @param remoteids :  ovh4,ovh5:2222

        to test
        js 'c=j.tools.cuisine.get("192.168.0.149");c.installer.sshreflector_client("ovh4,ovh5:2222")'

        """

        if remoteids.find(",")!=-1:
            for item in remoteids.split(","):
                self.sshreflector_client(item.strip())
        else:

            self.client_delete()

            self.cuisine.ns.hostfile_set_fromlocal()

            remotecuisine=j.tools.cuisine.get(remoteids)

            package="autossh"
            self.cuisine.package.install(package)

            lpath=os.environ["HOME"]+"/.ssh/reflector"

            if reset or not j.sal.fs.exists(lpath) or not j.sal.fs.exists(lpath_pub):
                print("DOWNLOAD SSH KEYS")
                #get private key from reflector
                ftp=remotecuisine.core.executor.sshclient.getSFTP()
                path="/home/sshreflector/.ssh/reflector"
                ftp.get(path,lpath)
                ftp.get(path+".pub",lpath+".pub")
                ftp.close()

            #upload to reflector client
            ftp=self.cuisine.core.executor.sshclient.getSFTP()
            rpath="/root/.ssh/reflector"
            ftp.put(lpath,rpath)
            ftp.put(lpath+".pub",rpath+".pub")
            self.cuisine.core.run("chmod 0600 /root/.ssh/reflector")
            self.cuisine.core.run("chmod 0600 /root/.ssh/reflector.pub")

            if(remotecuisine.core.executor.addr.find(".")!=-1):
                #is real ipaddress, will put in hostfile as reflector
                addr=remotecuisine.core.executor.addr
            else:
                a=socket.gethostbyaddr(remotecuisine.core.executor.addr)
                addr=a[2][0]

            port=remotecuisine.core.executor.port

            #test if we can reach the port
            if j.sal.nettools.tcpPortConnectionTest(addr,port)==False:
                raise j.exceptions.RuntimeError("Cannot not connect to %s:%s"%(addr,port))


            rname="refl_%s"%remotecuisine.core.executor.addr.replace(".","_")
            rname_short=remotecuisine.core.executor.addr.replace(".","_")

            self.cuisine.ns.hostfile_set(rname,addr)

            if remotecuisine.core.file_exists("/home/sshreflector/reflectorclients")==False:
                print ("reflectorclientsfile does not exist")
                remotecuisine.core.file_write("/home/sshreflector/reflectorclients","%s:%s\n"%(self.cuisine.platformtype.hostname,9800))
                newport=9800
                out2=remotecuisine.core.file_read("/home/sshreflector/reflectorclients")
            else:
                remotecuisine.core.file_read("/home/sshreflector/reflectorclients")
                out=remotecuisine.core.file_read("/home/sshreflector/reflectorclients")
                out2=""
                newport=0
                highestport=0
                for line in out.split("\n"):
                    if line.strip()=="":
                        continue
                    if line.find(self.cuisine.platformtype.hostname)!=-1:
                        newport=int(line.split(":")[1])
                        continue
                    foundport=int(line.split(":")[1])
                    if foundport>highestport:
                        highestport=foundport
                    out2+="%s\n"%line
                if newport==0:
                    newport=highestport+1
                out2+="%s:%s\n"%(self.cuisine.platformtype.hostname,newport)
                remotecuisine.core.file_write("/home/sshreflector/reflectorclients",out2)

            self.cuisine.core.file_write("/etc/reflectorclients",out2)

            reflport="9222"

            print("check ssh connection to reflector")
            self.cuisine.core.run("ssh -i /root/.ssh/reflector -o StrictHostKeyChecking=no sshreflector@%s -p %s 'ls /'"%(rname,reflport))
            print ("OK")

            cpath=self.cuisine.core.run("which autossh")
            cmd="%s -M 0 -N -o ExitOnForwardFailure=yes -o \"ServerAliveInterval 60\" -o \"ServerAliveCountMax 3\" -R %s:localhost:22 sshreflector@%s -p %s -i /root/.ssh/reflector"%(cpath,newport,rname,reflport)
            self.cuisine.processmanager.ensure("autossh_%s"%rname_short, cmd, descr='')

            print ("On %s:%s remote SSH port:%s"%(remotecuisine.core.executor.addr,port,newport))


    # @actionrun()
    def createconnection(self,remoteids):
        """
        @param remoteids are the id's of the reflectors e.g. 'ovh3,ovh5:3333'
        """
        self.cuisine.core.run("killall autossh",die=False)
        self.cuisine.package.install("autossh")


        if remoteids.find(",")!=-1:
            cuisine=None
            for item in remoteids.split(","):
                try:
                    cuisine=j.tools.cuisine.get(item)
                except:
                    pass
        else:
            cuisine=j.tools.cuisine.get(remoteids)
        if cuisine==None:
            raise j.exceptions.RuntimeError("could not find reflector active")

        rpath="/home/sshreflector/reflectorclients"
        lpath=os.environ["HOME"]+"/.ssh/reflectorclients"
        ftp=cuisine.core.executor.sshclient.getSFTP()
        ftp.get(rpath,lpath)

        out=self.cuisine.core.file_read(lpath)

        addr=cuisine.core.executor.addr

        keypath=os.environ["HOME"]+"/.ssh/reflector"

        for line in out.split("\n"):
            if line.strip()=="":
                continue
            name,port=line.split(":")

            # cmd="ssh sshreflector@%s -o StrictHostKeyChecking=no -p 9222 -i %s -L %s:localhost:%s"%(addr,keypath,port,port)
            # self.cuisine.tmux.executeInScreen("ssh",name,cmd)

            cmd="autossh -M 0 -N -f -o ExitOnForwardFailure=yes -o \"ServerAliveInterval 60\" -o \"ServerAliveCountMax 3\" -L %s:localhost:%s sshreflector@%s -p 9222 -i %s"%(port,port,addr,keypath)
            self.cuisine.core.run(cmd)


        print ("\n\n\n")
        print ("Reflector:%s"%addr)
        print (out)



    def __str__(self):
        return "cuisine.reflector:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))


    __repr__=__str__
