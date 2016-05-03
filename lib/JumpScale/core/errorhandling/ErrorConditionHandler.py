import sys
import traceback
import inspect

from JumpScale import j
from JumpScale.core.errorhandling.ErrorConditionObject import ErrorConditionObject

class ErrorConditionHandler():

    def __init__(self,haltOnError=True,storeErrorConditionsLocal=True):
        self.__jslocation__ = "j.errorconditionhandler"
        self._blacklist = None
        self.lastAction=""
        self.haltOnError=haltOnError
        self.lastEco=None
        self.escalateToRedis=None

    def getErrorConditionObject(self,ddict={},msg="",msgpub="",category="",level=1,type="UNKNOWN",tb=None):
        """
        @data is dict with fields of errorcondition obj
        returns only ErrorConditionObject which should be used in jumpscale to define an errorcondition (or potential error condition)

        """
        errorconditionObject= ErrorConditionObject(ddict=ddict,msg=msg,msgpub=msgpub,level=level,category=category,type=type,tb=tb)
        return errorconditionObject

    def processPythonExceptionObject(self,exceptionObject, tb=None):
        """
        how to use

        try:
            ##do something
        except Exception,e:
            j.errorconditionhandler.processexceptionObject(e)

        @param exceptionObject is errorobject thrown by python when there is an exception
        @param ttype : is the description of the error, can be None
        @param tb : can be a python data object for traceback, can be None

        @return [ecsource,ecid,ecguid]

        the errorcondition is then also processed e.g. send to local logserver and/or stored locally in errordb
        """
        eco=self.parsePythonExceptionObject(exceptionObject,ttype, tb,level,message)
        eco.process()

    def parsePythonExceptionObject(self,exceptionObject,tb=None):

        """
        how to use

        try:
            ##do something
        except Exception,e:
            eco=j.errorconditionhandler.parsePythonExceptionObject(e)

        eco is jumpscale internal format for an error
        next step could be to process the error objecect (eco) e.g. by eco.process()

        @param exceptionObject is errorobject thrown by python when there is an exception
        @param ttype : is the description of the error, can be None
        @param tb : can be a python data object for traceback, can be None

        @return a ErrorConditionObject object as used by jumpscale (should be the only type of object we pass around)


        """

        #this allows to do raise eco
        if isinstance(exceptionObject, ErrorConditionObject):  #was BaseException  , dont understand (despiegk)
            # return self.getErrorConditionObject(exceptionObject.eco)
            return ErrorConditionObject

        if not isinstance(exceptionObject, Exception):
            print ("did not receive an Exceptio object for python exception, this is serious bug.")
            print ("exceptionObject was:\n%s"%exceptionObject)
            sys.exit(1)

        if tb==None:
            ttype, exc_value, tb=sys.exc_info()

        if hasattr(exceptionObject,"codetrace"):
            codetrace=exceptionObject.codetrace
        else:
            codetrace=True

        if hasattr(exceptionObject,"whoami"):
            whoami=exceptionObject.whoami
        else:
            whoami=""

        if hasattr(exceptionObject,"eco"):
            eco=exceptionObject.eco
        else:
            eco=None

        if hasattr(exceptionObject,"level"):
            level=exceptionObject.level
        else:
            level=1

        if hasattr(exceptionObject,"actionkey"):
            actionkey=exceptionObject.actionkey
        else:
            actionkey=""


        if hasattr(exceptionObject,"msgpub"):
            msgpub=exceptionObject.msgpub
        else:
            msgpub=""

        if hasattr(exceptionObject,"source"):
            source=exceptionObject.source
        else:
            source=""

        if hasattr(exceptionObject,"type"):
            type=exceptionObject.type
        else:
            type="UNKNOWN"

        if hasattr(exceptionObject,"actionkey"):
            actionkey=exceptionObject.actionkey
        else:
            actionkey=""

        if hasattr(exceptionObject,"message"):
            message=exceptionObject.message
        else:
            message=str(exceptionObject)

        # if ttype!=None:
        #     try:
        #         type_str=str(ttype).split("exceptions.")[1].split("'")[0]
        #     except:
        #         type_str=str(ttype)
        # else:
        #     type_str=""

        if eco==None:
            eco=self.getErrorConditionObject(msg=message,msgpub=msgpub,level=level,tb=tb,type=type)

        if codetrace:
            #so for unknown exceptions not done through raise j.exceptions we will do stacktrace
            eco.tracebackSet(tb,exceptionObject)

            if len(eco.traceback)>10000:
                eco.traceback=errorobject.traceback[:10000]

        # if "message" in exceptionObject.__dict__:
        #     errorobject.exceptioninfo = j.data.serializer.json.dumps({'message': exceptionObject.message})
        # else:
        #     errorobject.exceptioninfo = j.data.serializer.json.dumps({'message': str(exceptionObject)})

        eco.exceptionclassname = exceptionObject.__class__.__name__

        # module = inspect.getmodule(exceptionObject)
        # errorobject.exceptionmodule = module.__name__ if module else None

        # try:
        #     errorobject.funcfilename=tb.tb_frame.f_code.co_filename
        # except:
        #     pass

        # # try:
        # try:
        #     backtrace = "~ ".join([res for res in traceback.format_exception(ttype, exceptionObject, tb)])
        #     if len(backtrace)>10000:
        #         backtrace=backtrace[:10000]
        #     errorobject.backtrace=backtrace
        # except:
        #     print("ERROR in trying to get backtrace")

        # except Exception,e:
        #     print "CRITICAL ERROR in trying to get errorobject, is BUG, please check (ErrorConditionHandler.py on line 228)"
        #     print "error:%s"%e
        #     sys.exit()


        return eco
