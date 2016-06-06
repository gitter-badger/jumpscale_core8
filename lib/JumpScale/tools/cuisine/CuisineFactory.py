from JumpScale import j

from Cuisine2 import *

class JSCuisineFactory:
    def __init__(self):
        self.__jslocation__ = "j.tools.cuisine"
        self._local=None
        self._cuinses_instance = {}

    @property
    def local(self):
        if self._local is None:
            self._local = JSCuisine(j.tools.executor.getLocal())
        return self._local

    def getPushKey(self,addr='localhost:22',login="root",passwd="",keyname="",pubkey=""):
        """
        will try to login if not ok then will try to push key with passwd
        will push local key to remote, if not specified will list & you can select
        if passwd not specified will ask
        @param pubkey is the pub key to use (is content of key)
        """
        if addr.find(":")!=-1:
            addr,port=addr.split(":",1)
            addr=addr.strip()
            port=int(port.strip())
        else:
            port=22

        executor=None
        if passwd=="":
            #@todo fix (*1*),goal is to test if ssh works, get some weird paramiko issues or timeout is too long
            res=j.clients.ssh.get(addr, port=port, login=login, passwd="",allow_agent=True, look_for_keys=True,timeout=0.5,testConnection=True,die=False)
            if res!=False:
                executor=j.tools.executor.getSSHBased(addr=addr, port=port,login=login)
            else:
                passwd=j.tools.console.askPassword("please specify root passwd",False)

        if pubkey=="" and executor==None:
            if keyname=="":
                rc,out=j.sal.process.execute("ssh-add -l")
                keys=[]
                for line in out.split("\n"):
                    try:
                        #ugly needs to be done better
                        item=line.split(" ",2)[2]
                        keyname=item.split("(",1)[0].strip()
                        keys.append(keyname)
                    except:
                        pass
                key=j.tools.console.askChoice(keys,"please select key")
            else:
                key=keyname
        else:
            key=None

        if executor==None:
            executor=j.tools.executor.getSSHBased(addr=addr, port=port,login=login,passwd=passwd,pushkey=key,pubkey=pubkey)

        j.clients.ssh.cache={}
        executor=j.tools.executor.getSSHBased(addr=addr, port=port,login=login)#should now work with key only

        cuisine = JSCuisine(executor)
        self._cuinses_instance[executor.id] = cuisine
        return self._cuinses_instance[executor.id]

    def get(self,executor=None):

        """
        example:
        executor=j.tools.executor.getSSHBased(addr='localhost', port=22,login="root",passwd="1234",pushkey="ovh_install")
        cuisine=j.tools.cuisine.get(executor)

        executor can also be a string like: 192.168.5.5:9022

        or if used without executor then will be the local one
        """
        executor = j.tools.executor.get(executor)
        if executor.id in self._cuinses_instance:
            return self._cuinses_instance[executor.id]

        cuisine = JSCuisine(executor)
        self._cuinses_instance[executor.id] = cuisine
        return self._cuinses_instance[executor.id]

    def getFromId(self, id):
        executor = j.tools.executor.get(id)
        return self.get(executor)
