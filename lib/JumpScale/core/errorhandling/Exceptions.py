from JumpScale import j


class BaseJSException(Exception):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        if j.data.types.string.check(level):
            level=1
            tags="cat:%s"%level
        super().__init__(message)
        # j.errorconditionhandler.setExceptHook()
        try:
            btkis,filename0,linenr0,func0=j.exceptionutils.getErrorTraceKIS(tb=tb)
        except:
            btkis,filename0,linenr0,func0=None,None,None,None
        self.message = message
        self.level = level
        self.source = source
        self.type = ""
        self.actionkey = actionkey
        self.eco = eco
        self.codetrace = True
        self._tags_add = tags
        self.msgpub = msgpub
        self.whoami = j.application.getWhoAmiStr()
        if self.whoami == "0_0_0":
            self.whoami = ""

        self.appname=j.application.appname
        self.gid = j.application.whoAmI.gid
        self.nid = j.application.whoAmI.nid
        self.pid = j.application.whoAmI.pid
        self.epoch= j.data.time.getTimeEpoch()

    @property
    def tags(self):
        msg = ""
        if self.level != 1:
            msg += "level:%s " % self.level
        if self.source != "":
            msg += "source:%s " % self.source
        if self.type != "":
            msg += "type:%s " % self.type
        if self.actionkey != "":
            msg += "actionkey:%s " % self.actionkey
        if self._tags_add != "":
            msg += " %s " % self._tags_add
        return msg.strip()

    @property
    def msg(self):
        return "%s ((%s))" % (self.message, self.tags)

    def toJson(self):
        return self.__dict__

    def __str__(self):
        out = "ERROR: %s ((%s))" % (self.message, self.tags)
        return out

    __repr__ = __str__


class HaltException(BaseJSException):
    pass


class RuntimeError(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "runtime.error"
        self.codetrace = True


class Input(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "input.error"
        self.codetrace = True


class BUG(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "bug.js"
        self.codetrace = True


class JSBUG(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "bug.js"
        self.codetrace = True


class OPERATIONS(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "operations"
        self.codetrace = True


class IOError(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "ioerror"
        self.codetrace = False


class AYSNotFound(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "ays.notfound"
        self.codetrace = False


class NotFound(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "notfound"
        self.codetrace = False
