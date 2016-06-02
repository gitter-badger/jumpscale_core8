
from JumpScale import j
import random
import sys

class IDGenerator:
    """
    generic provider of id's
    lives at j.data.idgenerator
    """
    def __init__(self):
        self.__jslocation__ = "j.data.idgenerator"

    def generateRandomInt(self,fromInt,toInt):
        """
        how to use:  j.data.idgenerator.generateRandomInt(0,10)
        """
        return random.randint(fromInt,toInt)
        
    def generateIncrID(self,incrTypeId,service,reset=False):
        """
        type is like agent, job, jobstep
        needs to be a unique type, can only work if application service is known
        how to use:  j.data.idgenerator.generateIncrID("agent")
        @reset if True means restart from 1
        """
        key="incrementor_%s"%incrTypeId
        if service.db.exists(key) and reset==False:
            lastid=int(service.db.get(key))
            service.db.testAndSet(key,str(lastid),str(lastid+1))
            return lastid+1
        else:
            service.db.set(key,"1")
            return 1
    
    def getID(self,incrTypeId,objectUniqueSeedInfo,service,reset=False):
        """
        get a unique id for an object uniquely identified
        remembers previously given id's
        """
        key="idint_%s_%s" % (incrTypeId,objectUniqueSeedInfo)
        if service.db.exists(key) and reset==False:
            id=int(service.db.get(key))
            return id
        else:
            id=self.generateIncrID(incrTypeId,service)            
            service.db.set(key,str(id))
            return id
        
    def generateGUID(self):
        """
        generate unique guid
        how to use:  j.data.idgenerator.generateGUID()
        """        
        import uuid
        return str(uuid.uuid4())

    def generateXCharID(self,x):
        r="1234567890abcdefghijklmnopqrstuvwxyz"
        l=len(r)
        out=""
        for i in range(0,x):
            p=self.generateRandomInt(0,l-1)
            out+=r[p]
        return out