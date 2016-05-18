
import sys, os, inspect
import tempfile

from JumpScale import j


def pathToUnicode(path):
    """
    Convert path to unicode. Use the local filesystem encoding. Will return
    path unmodified if path already is unicode.

    @param path: path to convert to unicode
    @type path: basestring
    @return: unicode path
    @rtype: unicode
    """
    if isinstance(path, str):
        return path

    return path.decode(sys.getfilesystemencoding())

class Dirs(object):
    """Utility class to configure and store all relevant directory paths"""


    def __init__(self):
        '''jumpscale sandbox base folder'''
        self.__jslocation__ = "j.dirs"
        self.__initialized = False ##bool

        import sys

        # self.base=j.application.config.get("system.paths.base")
        self.base = j.do.BASE
        if j.core.db!=None:
            data=j.core.db.get("system.dirs.%s"%self.base)
            if data!=None:
                self.__dict__=j.data.serializer.json.loads(data.decode())
            else:
                self.init()
    def init(self):
        print ("load dirs")
        self.appDir = j.application.config.get("system.paths.app")
        self.tmplsDir = j.application.config.get("system.paths.templates")
        self.varDir = j.application.config.get("system.paths.var")
        self.cfgDir = j.application.config.get("system.paths.cfg")
        self.libDir = j.application.config.get("system.paths.lib")
        self.jsLibDir = os.path.join(self.libDir,"JumpScale")
        #j.application.config.get("system.paths.python.lib.js")
        self.logDir = j.application.config.get("system.paths.log")
        self.pidDir = j.application.config.get("system.paths.pid")
        self.codeDir = j.application.config.get("system.paths.code")
        self.libExtDir = j.application.config.get("system.paths.python.lib.ext")
        self.tmpDir = tempfile.gettempdir()
        self.hrd =  os.path.join(j.application.config.get("system.paths.hrd"),"system")
        self.homeDir=os.environ["HOME"]

        self._ays=None

        self._createDir(os.path.join(self.base,"libext"))
        self._createDir(self.tmplsDir)

        if self.libDir in sys.path:
            sys.path.pop(sys.path.index(self.libDir))
        sys.path.insert(0,self.libDir)

        pythonzip = os.path.join(self.libDir, 'python.zip')
        if os.path.exists(pythonzip):
            if pythonzip in sys.path:
                sys.path.pop(sys.path.index(pythonzip))
            sys.path.insert(0,pythonzip)

        if self.libExtDir in sys.path:
            sys.path.pop(sys.path.index(self.libExtDir))
        sys.path.insert(2,self.libExtDir)

        if 'JSBASE' in os.environ:
            self.binDir = os.path.join(self.base, 'bin')
        else:
            self.binDir = j.application.config.get("system.paths.bin")

        data=j.data.serializer.json.dumps(self.__dict__)
        j.core.db.set("system.dirs.%s"%self.base,data)

    def replaceTxtDirVars(self,txt,additionalArgs={}):
        """
        replace $base,$vardir,$cfgDir,$bindir,$codedir,$tmpdir,$logdir,$appdir with props of this class
        """
        txt=txt.replace("$base",self.base)
        txt=txt.replace("$appdir",self.appDir)
        txt=txt.replace("$tmplsDir",self.tmplsDir)
        txt=txt.replace("$codedir",self.codeDir)
        txt=txt.replace("$vardir",self.varDir)
        txt=txt.replace("$cfgDir",self.cfgDir)
        # txt=txt.replace("$hrdDir",self.ays)
        txt=txt.replace("$bindir",self.binDir)
        txt=txt.replace("$logdir",self.logDir)
        txt=txt.replace("$tmpdir",self.tmpDir)
        txt=txt.replace("$libdir",self.libDir)
        txt=txt.replace("$jslibextdir",self.libExtDir)
        txt=txt.replace("$jsbindir",self.binDir)
        txt=txt.replace("$nodeid",str(j.application.whoAmI.nid))
        txt=txt.replace("$jumpscriptsdir", j.core.jumpscripts.basedir)
        for key,value in list(additionalArgs.items()):
            txt=txt.replace("$%s"%key,str(value))
        return txt

    def replaceFilesDirVars(self,path,recursive=True, filter=None,additionalArgs={}):
        if j.sal.fs.isFile(path):
            paths=[path]
        else:
            paths=j.sal.fs.listFilesInDir(path,recursive,filter)

        for path in paths:
            content=j.sal.fs.fileGetContents(path)
            content2=self.replaceTxtDirVars(content,additionalArgs)
            if content2!=content:
                j.sal.fs.writeFile(filename=path,contents=content2)

    def _createDir(self,path):
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except:
            pass


    # @property
    # def ays(self):
    #     if self._ays!=None:
    #         return self._ays
    #     path = j.atyourservice.basepath
    #     self._ays= j.sal.fs.joinPaths(path,"services")
    #     j.sal.fs.createDir(self._ays)
    #     return self._ays


    def _getParent(self, path):
        """
        Returns the parent of the path:
        /dir1/dir2/file_or_dir -> /dir1/dir2/
        /dir1/dir2/            -> /dir1/
        @todo why do we have 2 implementations which are almost the same see getParentDirName()
        """
        parts = path.split(os.sep)
        if parts[-1] == '':
            parts=parts[:-1]
        parts=parts[:-1]
        if parts==['']:
            return os.sep
        return os.sep.join(parts)

    def _getLibPath(self):
        parent = self._getParent
        libDir=parent(parent(__file__))
        libDir=os.path.abspath(libDir).rstrip("/")
        return libDir

    def getPathOfRunningFunction(self,function):
        return inspect.getfile(function)

    # def loadProtectedDirs(self):
    #     return
    #     protectedDirsDir = os.path.join(self.cfgDir, 'debug', 'protecteddirs')
    #     if not os.path.exists(protectedDirsDir):
    #         self._createDir(protectedDirsDir)
    #     _listOfCfgFiles = j.sal.fs.listFilesInDir(protectedDirsDir, filter='*.cfg')
    #     _protectedDirsList = []
    #     for _cfgFile in _listOfCfgFiles:
    #         _cfg = open(_cfgFile, 'r')
    #         _dirs = _cfg.readlines()
    #         for _dir in _dirs:
    #             _dir = _dir.replace('\n', '').strip()
    #             if j.sal.fs.isDir(_dir):
    #                 # npath=j.sal.fs.pathNormalize(_dir)
    #                 if _dir not in _protectedDirsList:
    #                     _protectedDirsList.append(_dir)
    #     self.protectedDirs = _protectedDirsList


    # def addProtectedDir(self,path,name="main"):
    #     if j.sal.fs.isDir(path):
    #         path=j.sal.fs.pathNormalize(path)
    #         configfile=os.path.join(self.cfgDir, 'debug', 'protecteddirs',"%s.cfg"%name)
    #         if not j.sal.fs.exists(configfile):
    #             j.sal.fs.writeFile(configfile,"")
    #         content=j.sal.fs.fileGetContents(configfile)
    #         if path not in content.split("\n"):
    #             content+="%s\n"%path
    #             j.sal.fs.writeFile(configfile,content)
    #         self.loadProtectedDirs()

    # def removeProtectedDir(self,path):
    #     path=j.sal.fs.pathNormalize(path)
    #     protectedDirsDir = os.path.join(self.cfgDir, 'debug', 'protecteddirs')
    #     _listOfCfgFiles = j.sal.fs.listFilesInDir(protectedDirsDir, filter='*.cfg')
    #     for _cfgFile in _listOfCfgFiles:
    #         _cfg = open(_cfgFile, 'r')
    #         _dirs = _cfg.readlines()
    #         out=""
    #         found=False
    #         for _dir in _dirs:
    #             _dir = _dir.replace('\n', '').strip()
    #             if _dir==path:
    #                 #found, need to remove
    #                 found=True
    #             else:
    #                 out+="%s\n"%_dir
    #         if found:
    #             j.sal.fs.writeFile(_cfgFile,out)
    #             self.loadProtectedDirs()


    # def checkInProtectedDir(self,path):
    #     return
    #     #@todo reimplement if still required
    #     path=j.sal.fs.pathNormalize(path)
    #     for item in self.protectedDirs :
    #         if path.find(item)!=-1:
    #             return True
    #     return False

    def __str__(self):
        return str(self.__dict__) #@todo P3 implement (thisnis not working)

    __repr__=__str__
