# import urllib.parse
try:
    import urllib.request, urllib.parse, urllib.error
except:
    import urllib.parse as urllib


from CifsFS import *
from FtpFS import *
from FileFS import *
from HttpFS import *
from SshFS import *
from JumpScale import j
import re

class CloudSystemFS:
    def __init__(self):
        self.__jslocation__ = "j.sal.cloudfs"
        self.logger = j.logger.get("j.sal.cloudfs")
        pass

    def sourcePathExists(self, sourcepath):
        src_fs = self._getSourceHandler(sourcepath)
        return src_fs.exists()

    def fileGetContents(self, url):
        tempfile = j.sal.fs.getTmpFilePath()
        self.copyFile(url, 'file://' + tempfile)
        content = j.sal.fs.fileGetContents(tempfile)
        j.sal.fs.remove(tempfile)
        return content

    def writeFile(self, url, content):
        tempfile = j.sal.fs.getTmpFilePath()
        j.sal.fs.writeFile(tempfile, content)
        self.copyFile('file://' + tempfile, url)
        j.sal.fs.remove(tempfile)

    """
    set of library actions which are used in cloud
    these are different from j.sal.fs in the fact they support more generic url's and are specific to moving data around on a cloud/network level
    extension which is linked onto j.sal.cloudfs.
    """
    def copyFile(self,sourcepath,destinationpath,tempdir=j.dirs.tmpDir):
        """
        export specified file to destination
        @todo needs to be copied onto cloudapi aswell

        @param sourcepath: location of the file to export
        @type sourcepath: string

        @param destinationpath: location to export the file to. e.g. cifs://login:passwd@10.10.1.1/systemnas
        @type destinationpath: string
        """
        # tested scenarios
        #
        # j.sal.cloudfs.copyFile('ftp://ftp.belnet.be/mirror/ftp.centos.org/HEADER.html',  'cifs://aserver:aserver@localhost/share/testje')
        # j.sal.cloudfs.copyFile('file:///tmp/src', 'cifs://aserver:aserver@localhost/share')
        # j.sal.cloudfs.copyFile('file:///tmp/src', 'ftp://localhost/anon/remote-ftp')
        # j.sal.cloudfs.copyFile('ftp://ftp.belnet.be/mirror/ftp.centos.org/HEADER.html', 'ftp://localhost/anon/remote-ftp')
        # j.sal.cloudfs.copyFile('file:///mnt/blubje' , 'sftp://aserver:aserver@localhost/home/aserver/Desktop/')
        # j.sal.cloudfs.copyFile('sftp://aserver:aserver@localhost/home/aserver/Desktop/bub', 'file:///mnt/blubje')
        # Determine the object we need to call
        self.logger.info("copyFile: from [%s] to [%s]" % ( sourcepath, destinationpath) )

        src_fs = self._getSourceHandler(sourcepath)
        dst_fs = self._getDestinationHandler(destinationpath)
        dst_fs.upload(src_fs.download())

        dst_fs.cleanup()
        src_fs.cleanup()

    def moveFile(self,sourcepath, destinationpath, tempdir=j.dirs.tmpDir):
        """
        Move a file
        """
        self.logger.info("moveFile: from [%s] to [%s]" % ( sourcepath, destinationpath) )

        src_fs = self._getSourceHandler(sourcepath, Atype='move')
        dst_fs = self._getDestinationHandler(destinationpath, Atype='move')
        dst_fs.upload(src_fs.download())

        dst_fs.cleanup()
        src_fs.cleanup()

    def copyDir(self,sourcepath, destinationpath, tempdir=j.dirs.tmpDir, recursive=True):
        """
        Copy Directory
        """
        self.logger.info("copyDir: from [%s] to [%s]" % ( sourcepath, destinationpath) )

        src_fs = self._getSourceHandler(sourcepath, is_dir=True,  Atype='copy')
        dst_fs = self._getDestinationHandler(destinationpath, is_dir=True, Atype='copy')
        dst_fs.upload(src_fs.download())

        dst_fs.cleanup()
        src_fs.cleanup()

    def moveDir(self,sourcepath, destinationpath, tempdir=j.dirs.tmpDir, recursive=True):
        """
        Move directory
        """
        self.logger.info("moveDir: from [%s] to [%s]" % ( sourcepath, destinationpath) )

        src_fs = self._getSourceHandler(sourcepath, is_dir=True,  Atype='move')
        dst_fs = self._getDestinationHandler(destinationpath, is_dir=True, Atype='move')
        dst_fs.upload(src_fs.download())

        dst_fs.cleanup()
        src_fs.cleanup()

    def _getSourceHandler(self, sourcepath, is_dir=False,recursive=True, tempdir=j.dirs.tmpDir, Atype='copy'):
        """
        Handle all protocol related stuff
        Returns a dict with the src and dst
        """

        src_proto = self._determineProtocol(sourcepath)
        if(src_proto == "cifs" or src_proto == "smb"):
            src_elements = self._parseCifsURL(sourcepath)
        else:
            src_elements = urllib.urlparse(sourcepath)

        self.logger.info('PARSING SRC RETURNED %s' %str(src_elements))

        # Determine the object we need to call
        self.logger.info("_getSourceHandler: source protocol [%s]" % (src_proto))

        # for the source
        if(src_proto == "cifs" or src_proto == "smb"):
            src_fs = CifsFS('src',server=src_elements.hostname,share=src_elements.path,username=src_elements.username,password=src_elements.password,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        elif (src_proto == "ftp"):
            src_fs = FtpFS('src',server=src_elements.hostname,path=src_elements.path,username=src_elements.username,password=src_elements.password,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        elif (src_proto == 'file'):
            src_fs = FileFS('src',path=src_elements.path,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        elif (src_proto == 'http'):
            src_fs = HttpFS('src', server=src_elements.netloc,path=src_elements.path,tempdir=tempdir, Atype=Atype)
        elif (src_proto == 'sftp'):
            src_fs = SshFS('src', server=src_elements.hostname,directory=src_elements.path,username=src_elements.username,password=src_elements.password,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        else:
            q.eventhandler.raiseError('Unsupported protocol [%s] for the sourcepath [%s]'%(src_proto, sourcepath))

        return src_fs

    def _getDestinationHandler(self,destinationpath,is_dir=False,recursive=True, tempdir=j.dirs.tmpDir, Atype='copy'):
        """
        Handle all protocol related stuff
        Returns a dict with the src and dst
        """

        dst_proto = self._determineProtocol(destinationpath)
        if(dst_proto == "cifs" or dst_proto == "smb"):
            dst_elements = self._parseCifsURL(destinationpath)
        else:
            dst_elements = urllib.urlparse(destinationpath)
        self.logger.info('PARSING DEST RETURNED %s' %str(dst_elements))

        # Determine the object we need to call
        self.logger.info("_getDestinationHandler: destination protocol [%s]" % (dst_proto))

        if(dst_proto == "cifs" or dst_proto == "smb"):
            dst_fs = CifsFS('dst',server=dst_elements.hostname,share=dst_elements.path,username=dst_elements.username,password=dst_elements.password,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        elif (dst_proto == 'ftp'):
            dst_fs = FtpFS('dst',server=dst_elements.hostname,path=dst_elements.path,username=dst_elements.username,password=dst_elements.password,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        elif (dst_proto == 'file'):
            dst_fs = FileFS('dst',path=dst_elements.path,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        elif (dst_proto == 'http'):
            raise j.exceptions.RuntimeError('http as a destination is not supported')
        elif (dst_proto == 'sftp'):
            dst_fs = SshFS('dst', server=dst_elements.hostname,directory=dst_elements.path,username=dst_elements.username,password=dst_elements.password,is_dir=is_dir,recursive=recursive,tempdir=tempdir, Atype=Atype)
        else:
            q.eventhandler.raiseError('Unsupported protocol [%s] for the destinationpath [%s]'%(dst_proto, destinationpath))
        return dst_fs

    def _determineProtocol(self, url):
        """
        Determine the protocol to be used e.g ftp,cifs,rsync,...
        """
        elements = urllib.urlparse(url)
        self.logger.info('Determined protocol: %s' %str(elements.scheme))
        return elements.scheme

    def _parseCifsURL(self,url):
        """
        If URL starts with cifs:// we need to parse it ourselves since urllib does not support this
        """
        # Warning: Dirty HACK since urllib does not support cifs/smb but the URI is the same as ftp or http
        durl = url
        durl = durl.replace("cifs://","ftp://")
        durl = durl.replace("smb://","ftp://")

        elements = urllib.urlparse(durl)
        ret_elements = {}
        self.logger.info('_parseCifsURL returned %s' %elements.hostname)
        return elements

    def importFile(self,sourcepath,destinationpath,tempdir=j.dirs.tmpDir):
        """
        import specified file to machine path
        @todo needs to be copied onto cloudapi aswell

        @param sourcepath: location to import the file from. e.g. ftp://login:passwd@10.10.1.1/myroot/drive_c_kds.vdi
        @type sourcepath: string

        @param destinationpath: location to import the file to (i.e.full path on machine)
        @type destinationpath: string
        """
        self.copyFile(sourcepath,destinationpath,tempdir=tempdir)

    def exportDir(self,sourcepath,destinationpath,recursive=True,tempdir=j.dirs.tmpDir):
        """
        export specified folder to destination
        @todo needs to be copied onto cloudapi aswell

        @param sourcepath:       location to export. e.g. ftp://login:passwd@10.10.1.1/myroot/drive_c_kds.vdi
        @type sourcepath:        string

        @param destinationpath:  location to export the dir to
        @type destinationpath:   string

        @param recursive:        if true will include all sub-directories
        @type recursive:         boolean
        """

        # Tested: j.sal.cloudfs.importDir('smb://autotest:phun5chU@fileserver.aserver.com/Public/Engineering/vdi/sso_images/SSO_VD', 'file:///tmp/tmp/')
        self.logger.info("exportDir: from [%s] to [%s]" % (sourcepath, destinationpath) )

        src_fs = self._getSourceHandler(sourcepath, is_dir=True,  Atype='copy')
        dst_fs = self._getDestinationHandler(destinationpath, is_dir=True, Atype='copy')
        dst_fs.upload(src_fs.download())

        dst_fs.cleanup()
        src_fs.cleanup()

    def importDir(self,sourcepath,destinationpath,tempdir=j.dirs.tmpDir):
        """
        import specified dir to machine path
        @todo needs to be copied onto cloudapi aswell

        @param sourcepath: location to import the dir from. e.g. ftp://login:passwd@10.10.1.1/myroot/mymachine1/
        @type sourcepath: string

        @param destinationpath: location to import the dir to (i.e.full path on machine)
        @type destinationpath: string
        """
        self.exportDir(sourcepath,destinationpath)

    def exportVolume(self,sourcepath,destinationpath,format="vdi",tempdir=j.dirs.tmpDir):
        """
        export volume to a e.g. VDI


        @param sourcepath:         device name of the volume to export e.g.  E: F on windows, or /dev/sda5 on linux
        @type sourcepath:          string

        @param destinationpath:    location to export the volume to e.g. ftp://login:passwd@10.10.1.1/myroot/mymachine1/test.vdi, if .vdi.tgz at end then compression will happen automatically
        @type destinationpath:     string
        @param tempdir:            (optional) directory to use as temporary directory, for cifs/smb tempdir can be None which means: export directly over CIFS
        @type tempdir:             string
        """
        prefix = 'file://'
        copy   = True

        if not tempdir and self._determineProtocol(destinationpath) in ("cifs", "smb"):
            destination = self._getDestinationHandler(destinationpath=destinationpath)
            CifsFS._connect(destination)
            directory = destination.mntpoint
            if not j.sal.fs.exists(directory):
                j.sal.fs.createDir(directory)
            tmp_outputFileName = '%s/%s'%(directory,destination.filename)
            copy = False
        else:
            tmp_outputFileName = j.sal.fs.getTempFileName(tempdir)

        self.logger.info("CloudSystemFS: exportVolume source [%s] to path [%s]" % (sourcepath, tmp_outputFileName))

        if destinationpath.endswith('.tgz'):
            compressImage = True
        else:
            compressImage = False

        j.sal.qemu_img.convert(sourcepath, 'raw', tmp_outputFileName, format, compressTargetImage=compressImage)
        outputFileName = ''.join([prefix,tmp_outputFileName])

        if copy:
            self.copyFile(outputFileName,destinationpath,tempdir=tempdir)
            j.sal.fs.remove(tmp_outputFileName)
        else:
            destination.cleanup()

    def importVolume(self, sourcepath, destinationpath,format='vdi',tempdir=j.dirs.tmpDir):
        """
        Import volume from specified source

        @param sourcepath: location to import the volume from e.g. ftp://login:passwd@10.10.1.1/myroot/mymachine1/test.vdi, if .vdi.tgz at end then compression will happen automatically
        @type sourcepath: string

        @param destinationpath: name of the device to import to e.g.  E: F on windows, or /dev/sda5 on linux
        @type destinationpath: string
        @param tempdir:            (optional) directory whereto will be exported; default is the default temp-directory as determined by underlying system
        @type tempdir:             string
        """
        prefix = 'file://'
        self.logger.info("CloudSystemFS: importVolume source [%s] to path [%s]" % (sourcepath, destinationpath))

        if sourcepath.endswith('.tgz'):
            compressImage = True
        else:
            compressImage = False

        protocol = self._determineProtocol(sourcepath)
        if  protocol == "file":
            elements = urllib.urlparse(sourcepath)
            self.logger.info("Source is a local file:// not running copyFile... for %s" % elements.path)
            tmp_inputFileName = elements.path
        elif protocol == "smb" or protocol == "cifs":
            src_elements = self._parseCifsURL(sourcepath)
            src_fs = CifsFS('src',server=src_elements.hostname,share=src_elements.path,username=src_elements.username,password=src_elements.password,is_dir=False,recursive=False,tempdir=tempdir)
            tmp_inputFileName = src_fs.download()
            self.logger.info("Source is a CIFS/SMB share, not running copyFile,using %s" %tmp_inputFileName)
        else:
            tmp_inputFileName = j.sal.fs.getTempFileName(tempdir)
            self.copyFile(sourcepath, ''.join([prefix,tmp_inputFileName]),tempdir=tempdir)

        j.sal.qemu_img.convert(tmp_inputFileName, format, destinationpath, 'raw', compressTargetImage=compressImage)

        if not protocol == "file" and not protocol == "smb" and not protocol == "cifs":
            j.sal.fs.remove(tmp_inputFileName)
        elif protocol == "smb" or protocol == "cifs":
            src_fs.cleanup()

    def listDir(self, path):
        """
        List content of specified path
        """
        is_dir = True
        recursive = False

        self.logger.info("listDir: supplied path is [%s]" % path )

        proto = self._determineProtocol(path)
        if(proto == "cifs" or proto == "smb"):
            path_elements = self._parseCifsURL(path)
            self.logger.info('CIFS LISTDIR path_elements: %s' %str(path_elements))
        else:
            path_elements = urllib.urlparse(path)

        # Determine the object we need to call
        self.logger.info("listDir: protocol [%s]" % proto )

        # for the source
        if(proto == "cifs" or proto == "smb"):
            fs = CifsFS('src',server=path_elements.hostname,share=path_elements.path,username=path_elements.username,password=path_elements.password,is_dir=is_dir,recursive=recursive)
        elif (proto == "ftp"):
            fs = FtpFS('src',server=path_elements.hostname,path=path_elements.path,username=path_elements.username,password=path_elements.password,is_dir=is_dir,recursive=recursive)
        elif (proto == 'file'):
            fs = FileFS('src',path=path_elements.path,is_dir=is_dir,recursive=recursive)
        elif (proto == 'sftp'):
            fs = SshFS('src', server=path_elements.hostname,directory=path_elements.path,username=path_elements.username,password=path_elements.password,is_dir=is_dir,recursive=recursive)
        else:
            q.eventhandler.raiseError('Unsupported protocol [%s] for the path [%s]'%(proto, path))

        dir_list = fs.list()
        fs.cleanup()

        return dir_list
