import traceback
from JumpScale import j
import sys
import time
import inspect

class ExceptionUtils:
    def __init__(self,haltOnError=True,storeErrorConditionsLocal=True):
        self.__jslocation__ = "j.exceptionutils"
        self.logger = j.logger.get("j.exceptionutils")
        self._escalateToRedis = None
        self._escalateToRedisPopulated = False
        self.setExceptHook()

    @property
    def escalateToRedis(self):
        if not self._escalateToRedisPopulated:
            self._escalateToRedisPopulated = True
            luapath = "%s/core/errorhandling/eco.lua" % j.dirs.jsLibDir
            if j.sal.fs.exists(path=luapath):
                lua = j.sal.fs.fileGetContents(luapath)
                self._escalateToRedis = j.core.db.register_script(lua)
        return self._escalateToRedis
    
    def setExceptHook(self):
        sys.excepthook = self.excepthook

    def getId(self, json):
        return j.data.hash.md5_string(','.join('%s:%s'%(i, json[i]) for i in sorted(json.keys()) if i not in ["epoch"]))

    def toJson(self, ttype, exceptionObject, tb):
        if (hasattr(exceptionObject,'toJson')):
            json = exceptionObject.toJson()
        else:
            json = {
                "msg": str(exceptionObject),
                "type": ttype.__name__,
            }
        json["id"] = self.getId(json)
        json["epoch"] = time.time()
        return json

    def _send2Redis(self, ttype, exceptionObject, tb):
        if self.escalateToRedis is not None:
            json = self.toJson(ttype, exceptionObject, tb)
            data = j.data.serializer.json.dumps(json)
            res = self.escalateToRedis(keys=["queues:eco","eco:%s"%(json["id"])],args=[data])
            return j.data.serializer.json.loads(res)

    def store(self, ttype=None, exceptionObject=None, tb=None):
        if (ttype, exceptionObject, tb) == (None, None, None):
            ttype, exceptionObject, tb = sys.exc_info()
        return self._send2Redis(ttype, exceptionObject, tb)

    def excepthook(self, ttype, exceptionObject, tb):
        """ every fatal error in jumpscale or by python itself will result in an exception
        in this function the exception is caught.
        This routine will create an errorobject & escalate to the infoserver
        @ttype : is the description of the error
        @tb : can be a python data object or a Event
        """
        self.logger.error_tb(ttype, exceptionObject, tb)
        # self.store(ttype, exceptionObject, tb)

    def getErrorTraceKIS(self,tb=None):
        out=[]
        nr=1
        filename0="unknown"
        linenr0=0
        func0="unknown"
        frs=self.getFrames(tb=tb)
        frs.reverse()
        for f,linenr in frs:
            try:
                code,linenr2=inspect.findsource(f)
            except Exception:
                continue
            start=max(linenr-10,0)
            stop=min(linenr+4,len(code))
            code2="".join(code[start:stop])
            finfo=inspect.getframeinfo(f)
            linenr3=linenr-start-1
            out.append((finfo.filename,finfo.function,linenr3,code2,linenr))
            if nr==1:
                filename0=finfo.filename
                linenr0=linenr
                func0=finfo.function

        return out,filename0,linenr0,func0
 
    def getFrames(self,tb=None):

        def _getitem_from_frame(f_locals, key, default=None):
            """
            f_locals is not guaranteed to have .get(), but it will always
            support __getitem__. Even if it doesnt, we return ``default``.
            """
            try:
                return f_locals[key]
            except Exception:
                return default

        if tb==None:
            ttype,msg,tb=sys.exc_info()

        if tb==None:
            frames=[(item[0],item[2]) for item in inspect.stack()]
        else:
            frames=[]
            while tb: #copied from sentry raven lib (BSD license)
                # support for __traceback_hide__ which is used by a few libraries
                # to hide internal frames.
                f_locals = getattr(tb.tb_frame, 'f_locals', {})
                if not _getitem_from_frame(f_locals, '__traceback_hide__'):
                    frames.append((tb.tb_frame, getattr(tb, 'tb_lineno', None)))
                tb = tb.tb_next
            frames.reverse()

        result=[]
        ignore=["ipython","errorcondition","loghandler","errorhandling"]
        for frame,linenr in frames:
            name=frame.f_code.co_filename
            # print "RRR:%s %s"%(name,linenr)
            name=name.lower()
            toignore=False
            for check in ignore:
                if name.find(check)!=-1:
                    toignore=True
            if not toignore:
                result.append((frame,linenr))

        return result