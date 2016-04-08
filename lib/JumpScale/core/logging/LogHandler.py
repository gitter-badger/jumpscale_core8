import itertools
import functools
from JumpScale import j
import re
import sys

import time
from datetime import datetime

from io import BytesIO





# SAFE_CHARS_REGEX = re.compile("[^ -~\n]")


def toolStripNonAsciFromText(text):
    """
    Filter out characters not between ' ' and '~' with an exception for
    newlines.

    @param text: text to strip characters from
    @type text: basestring
    @return: the stripped text
    @rtype: basestring
    """
    return SAFE_CHARS_REGEX.sub("", text)

class LogUtils(object):
    """
    Some log related utilities.
    """
    def trace(self, level=5, enabled=True):
        """
        Decorator factory. Use enabled to avoid the logging overhead when it's
        not needed. Do not the tracing can *not* be enabled or disabled at
        runtime.

        Typical usage:

        TRACING_ENABLED = True

        @j.logger.utils.trace(level=3, enabled=TRACING_ENABLED)
        def myFunc(arg1, arg2=12):
            ...

        @param level: level to log the calls on
        @type level: int
        @param enabled: whether or not to disable the tracing
        @type enabled: boolean
        @return: decorator factory
        @rtype: callable
        """

        if enabled:
            def decorator(func):
                """
                Decorator to log how and when the wrapped function is called.

                @param func: function to be wrapped
                @type func: callable
                @return: wrapped function
                @rtype: callable
                """
                @functools.wraps(func)
                def wrappedFunc(*args, **kwargs):
                    argiter = itertools.chain(args, ["%s=%s" % (k, v) for k, v in
                                                     list(kwargs.items())])
                    descr = "%s(%s)" % (func.__name__, ", ".join(argiter))
                    j.logger.log("Calling " + descr, level)
                    try:
                        return func(*args, **kwargs)
                    finally:
                        j.logger.log("Called " + descr, level)
                return wrappedFunc
        else:
            def decorator(func):
                return func
        return decorator

class LogItem(object):
    def __init__(self, message="", category="", tags="", level=5, jid="", parentjid="", masterjid="", private=False, epoch=0):
        self.message = message.strip().replace("\r\n", "/n").replace("\n", "/n")
        try:
            self.level = int(level)
        except:
            self.level=5
        self.category = category.replace(".", "_")
        if j.application.whoAmI:            
            self.gid = j.application.whoAmI.gid
            self.nid = j.application.whoAmI.nid            
            self.pid = j.application.whoAmI.pid

        self.appname = j.application.appname
        self.tags = str(tags).strip().replace("\r\n", "/n").replace("\n", "/n").replace("|", "/|")
        if jid=="" and j.application.jid!=0:
            self.jid=j.application.jid
        else:
            self.jid = str(jid)
        self.parentjid = str(parentjid)
        self.masterjid = str(masterjid)
        self.epoch = int(epoch) or j.data.time.getTimeEpoch()
        self.order = 0 #will be set by app which gets logs out of redis
        if private == True or int(private) == 1:
            self.private = 1
        else:
            self.private = 0

    def getSetGuid(self):
        """
        use osis to define & set unique guid (sometimes also id)
        """
        self.gid = int(self.gid)
        if self.pid!=0:
            self.guid = "%s_%s_%s"%(self.gid,self.pid,self.order)
        else:
            self.guid = "%s_%s_%s_%s"%(self.gid,self.nid,self.epoch,self.order)

        return self.guid

    def toJson(self):
        return j.data.serializer.json.dumps(self.__dict__)

    def __str__(self):
        if self.category!="":
            return "%s: %s" % (self.category.replace("_","."),self.message)
        else:
            ttime=time.strftime("%H:%M:%S: ", datetime.fromtimestamp(self.epoch).timetuple())
            message="%s %s %s%s" % (self.level, j.application.appname , ttime, self.message)
            return message

    __repr__ = __str__

class LogItemFromDict(LogItem):
    def __init__(self,ddict):
        self.__dict__=ddict

class LogHandlerArgs():
    def __init__(self):
        if j.core.db!=None:
            data=j.core.db.get("system.logging.%s"%j.dirs.base)
            if data!=None:
                self.__dict__=j.data.serializer.json.loads(data.decode())
                return
        print ("INITLOGS")
        self.maxlevel = 5
        self.consoleloglevel = 2
        self.consolelogCategories=[]
        self.enabled = j.application.config.getBool("system.logging",default=False)
        data=j.data.serializer.json.dumps(self.__dict__)
        j.core.db.set("system.logging.%s"%j.dirs.base,data)        

class LogHandler(object):
    def __init__(self):
        '''
        This empties the log targets
        '''
        self.__jslocation__ = "j.logger"
        self.utils = LogUtils()
        self.reset()     
        self.lastmessage = ""

        self.__dict__.update(LogHandlerArgs().__dict__)


    def init(self):
        if self.enabled:
            self.connectRedis()

    def connectRedis(self):
        # if j.sal.nettools.tcpPortConnectionTest("localhost", 9999, timeout=None):
        if j.core.db!=None:
            luapath="%s/core/logging/logs.lua"%j.dirs.jsLibDir
            if j.sal.fs.exists(path=luapath):
                lua=j.sal.fs.fileGetContents(luapath)
                self.redislogging=self.redis.register_script(lua)

    def _send2Redis(self,obj):
        return #@todo (***)
        if j.core.db!=None:# and self.redislogging!=None:
            data=obj.toJson()
            return self.redislogging(keys=["logs.queue"],args=[data])
        else:
            return None

    def getLogObjectFromDict(self, ddict):
        return LogItemFromDict(ddict)

    def nologger(self, func):
        """
        Decorator to disable logging for a specific method (probably not thread safe)
        """
        def wrapper(*args, **kwargs):
            previousvalue = self.enabled
            self.enabled = False
            try:
                return func(*args, **kwargs)
            finally:
                self.enabled = previousvalue
        return wrapper

    def nostdout(self):
        class NoStdout(object):
            def __init__(self):
                self._original_stderr = sys.stderr
                self._original_stdout = sys.stdout
                self._buffer = BytesIO()

            def __call__(self, func):
                def wrapper(*args, **kwargs):
                    with self:
                        return func(*args, **kwargs)
                return wrapper

            def __enter__(self):
                sys.stdout = self._buffer
                sys.stderr = self._buffer
                return self._buffer

            def __exit__(self, type, value, traceback):
                sys.stdout = self._original_stdout
                sys.stderr = self._original_stderr
                if type:
                    print((self._buffer.getvalue()))
                self._buffer.close()

        return NoStdout()

    def reset(self):
        self.maxlevel = 6
        self.consoleloglevel = 2
        self.consolelogCategories=[]
        self.lastmessage = ""
        # self.lastloglevel=0
        self.nolog = False
        self.enabled = True

    def disable(self):
        self.enabled = False
        if "console" in self.__dict__:
            self.console.disconnect()
            self.console = None

    def log(self, message, level=5, category="", tags="", jid="", parentjid="",masterjid="", private=False):
        """
        send to all log targets
        """
        # print "log: enabled:%s level:%s %s"%(self.enabled,level,message)

        if not self.enabled:
            return
            
        log = LogItem(message=message, level=level, category=category, tags=tags, jid=jid, parentjid=parentjid,masterjid=masterjid, private=private)

        if level < (self.consoleloglevel + 1):

            if self.consolelogCategories!=[]:
                for consolecat in self.consolelogCategories:
                    if log.category.find(consolecat)!=-1:
                        ccat=log.category
                        ccat=ccat[0:25]
                        j.tools.console.echo("%s - %-25s - %s"%(j.data.time.epoch2HRDateTime(log.epoch), ccat,log.message), log=False)
                        break
            else:
                j.tools.console.echo(str(log), log=False)
        
        if self.nolog:
            return

        if level < self.maxlevel+1 and (log.jid or log.category):
            #SEND TO REDIS
            return self._send2Redis(log)

        return None
