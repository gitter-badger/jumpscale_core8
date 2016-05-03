from JumpScale import j
import time
import imp
import linecache
import inspect
import multiprocessing
import tarfile
import io
import collections
import os
import base64

class Jumpscript(object):
    def __init__(self, ddict=None, path=None):
        self._loaded = False
        self.name=""
        self.organization=""
        self.period = 0
        self.lastrun = 0
        self.source=""
        self.debug = False
        self.path=path
        self.id = None
        self.startatboot = False
        self.path = path
        self.debug=False
        self.timeout = None
        if ddict:
            ddict.pop('path', None)
            self.__dict__.update(ddict)
        if path:
            self.load()
            self.loadAttributes()

    def write(self):
        if not self.path:
            jscriptdir = j.sal.fs.joinPaths(j.dirs.tmpDir,"jumpscripts")
            j.sal.fs.createDir(jscriptdir)
            self.path=j.sal.fs.joinPaths(jscriptdir, "%s_%s.py" % (self.organization, self.name))
        content="""
from JumpScale import j

"""
        content += self.source
        j.sal.fs.writeFile(filename=self.path, contents=content)

    def load(self):
        self._loaded = True
        md5sum = j.data.hash.md5_string(self.path)
        modulename = 'JumpScale.jumpscript_%s' % md5sum
        linecache.checkcache(self.path)
        self.module = imp.load_source(modulename, self.path)
        if self.source.find("DEBUG NOW")!=-1:
            self.debug=True

    def getDict(self):
        result = dict()
        for attrib in ('name', 'author', 'organization', 'category', 'license', 'version', 'roles', 'source', 'path', 'descr', 'queue', 'async', 'period', 'order', 'log', 'enable', 'startatboot', 'gid', 'id','timeout'):
            result[attrib] = getattr(self, attrib)
        return result

    def loadAttributes(self):
        name = getattr(self.module, 'name', "")
        if name=="":
            name=j.sal.fs.getBaseName(self.path)
            name=name.replace(".py","").lower()

        source = inspect.getsource(self.module)
        self.name=name
        self.author=getattr(self.module, 'author', "unknown")
        self.organization=getattr(self.module, 'organization', "unknown")
        self.category=getattr(self.module, 'category', "unknown")
        self.license=getattr(self.module, 'license', "unknown")
        self.version=getattr(self.module, 'version', "1.0")
        self.debug=getattr(self.module, 'debug', False)
        self.roles=getattr(self.module, 'roles', [])
        self.source=source
        self.descr=self.module.descr
        self.queue=getattr(self.module, 'queue', "")
        self.timeout=getattr(self.module, 'timeout', None)
        self.async = getattr(self.module, 'async',False)
        self.period=getattr(self.module, 'period',0)
        self.order=getattr(self.module, 'order', 1)
        self.log=getattr(self.module, 'log', True)
        self.enable=getattr(self.module, 'enable', True)
        self.startatboot=getattr(self.module, 'startatboot', False)
        self.gid=getattr(self.module, 'gid', j.application.whoAmI.gid)

    def getKey(self):
        return "%s_%s" % (self.organization, self.name)

    def executeInWorker(self, *args, **kwargs):
        if not self.path:
            self.write()
        if not self._loaded:
            self.load()

        if self.debug:
            result = self.executeInProcess(*args, **kwargs)
            return result
        else:
            def helper(pipe):
                try:
                    result = self.executeInProcess(*args, **kwargs)
                    pipe.send(result)
                except Exception as e:
                    result = "ERROR"
                    try:
                        result = self._getECO(e)
                    except:
                        pass
                    pipe.send((False, result))

            ppipe, cpipe = multiprocessing.Pipe()
            proc = multiprocessing.Process(target=helper, args=(cpipe,))
            proc.start()
            proc.join(self.timeout)
            if proc.is_alive():
                proc.terminate()
                return False, "TIMEOUT"
            return ppipe.recv()

    def _getECO(self, e):
        eco = j.errorconditionhandler.parsePythonExceptionObject(e)
        eco.tb = None
        eco.errormessage='Exec error procmgr jumpscr:%s_%s on node:%s_%s %s'%(self.organization,self.name, \
                j.application.whoAmI.gid, j.application.whoAmI.nid,eco.errormessage)
        eco.tags="jscategory:%s"%self.category
        eco.jid = j.application.jid
        eco.tags+=" jsorganization:%s"%self.organization
        eco.tags+=" jsname:%s"%self.name
        return eco

    def executeInProcess(self, *args, **kwargs):
        try:
            return True, self.module.action(*args, **kwargs)
        except Exception as e:
            print("error in jumpscript factory: execute in process.")
            eco = self._getECO(e)
            self.logger.warn_tb(j.exceptions.OPERATIONS, eco.errormessage, store=False)
            eco.parse()
            return False, eco


    def execute(self, *args, **kwargs):
        """
        """
        result = None, None
        redisw = kwargs.pop('_redisw', j.clients.redisworker)

        if not self.enable:
            return
        if not self.async:
            result = list(self.executeInProcess(*args, **kwargs))
            if not result[0]:
                eco = result[1]
                eco.type = str(eco.type)
                result[1] = eco.__dict__
        else:
            #make sure this gets executed by worker
            queue = getattr(self, 'queue', 'default') #fall back to default queue if none specified
            result=redisw.execJumpscript(self.id,_timeout=self.timeout,_queue=queue,_log=self.log,_sync=False)

        self.lastrun = time.time()
        if result!=None:
            print(("ok:%s"%self.name))
        return result


"""
Metadata about a Lua Jumpscript.
"""
LuaJumpscript = collections.namedtuple('LuaJumpscript', field_names=(
    'name', 'path', 'organization', 'queue', 'log', 'id',
))

class JumpscriptFactory:

    """
    """
    def __init__(self):
        self.__jslocation__ = "j.core.jumpscripts"
        self.basedir = j.sal.fs.joinPaths(j.dirs.base, 'apps', 'processmanager')

    def getJSClass(self):
        return Jumpscript

    def getArchivedJumpscripts(self, bz2_compressed=True, types=('processmanager', 'jumpscripts')):
        """
        Returns the available jumpscripts in TAR format that is optionally compressed using bzip2.

        Args:
            bz2_compressed (boolean): If True then the returned TAR is bzip2-compressed
            types (sequence of str): A sequence of the types of jumpscripts to be packed in the returned archive.
                possible values in the sequence are 'processmanager', 'jumpscripts', and 'luajumpscripts'.
        """
        fp = io.StringIO()
        with tarfile.open(fileobj=fp, mode='w:bz2' if bz2_compressed else 'w') as tar:
            for jumpscript_type in types:
                parent_path = '%s/apps/agentcontroller/%s' % (j.dirs.base, jumpscript_type)
                for allowed_filename_extension in ('py', 'lua'):
                    for file_path in j.sal.fs.walkExtended(parent_path, recurse=1, dirs=False,
                                                              filePattern='*.' + allowed_filename_extension):
                        path_in_archive = jumpscript_type + '/' + file_path.split(parent_path)[1]
                        tar.add(file_path, path_in_archive)
        return fp.getvalue()

    def loadFromAC(self, acl=None):
        raise NotImplementedError()
        # if acl is None:
        #     acl = j.clients.agentcontroller.getByInstance()
        # tar = base64.decodestring(acl.getJumpscripts())
        # self.loadFromTar(tar, 'bz2')

    def loadFromTar(self, tarcontent, type):
        import tarfile
        fp = io.StringIO()
        fp.write(tarcontent)
        fp.seek(0)
        mode = "r:%s" % type
        tar = tarfile.open(fileobj=fp, mode=mode)

        for tarinfo in tar:
            if tarinfo.isfile():
                print((tarinfo.name))
                if tarinfo.name.find("processmanager/")==0:
                    tar.extract(tarinfo.name, j.sal.fs.getParent(self.basedir))
                if tarinfo.name.find("jumpscripts/")==0:
                    tar.extract(tarinfo.name, self.basedir)

    @staticmethod
    def introspectLuaJumpscript(path):
        """
        Introspects for a Lua Jumpscript at the given path and returns a LuaJumpscript object with the results.

        Args:
            path (str): the absolute path to the jumpscript file.

        Raises:
            IOError if the file at the path could not be opened.
        """

        assert os.path.isabs(path), 'An absolute file path is needed'

        if not os.path.exists(path):
            raise IOError(path + ' does not exist')

        relative_path = path.split('agentcontroller/')[1]    # Remove the string "^.*agentcontroller/"

        # The Lua Jumpscript metadata is inferred conventionally using the jumpscript file's relative path as follows:
        # luajumpscripts/ORGANIZATION[/IRRELEVANT_SUBPATH]/JUMPSCRIPT_NAME.lua
        #
        # Note: The IRRELEVANT_SUBPATH is optional and is not used.

        path_components = relative_path.split('/')
        jumpscript_name = os.path.splitext(path_components[-1])[0]
        jumpscript_organization = path_components[1]

        return LuaJumpscript(
            name=jumpscript_name,
            path=path,
            organization=jumpscript_organization,
            queue=None,
            log=True,
            id=None,
        )
