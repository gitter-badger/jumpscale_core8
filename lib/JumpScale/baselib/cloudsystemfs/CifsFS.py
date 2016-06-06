from JumpScale import j
import os
import re

# requires smbfs package
class CifsFS:

    server = None
    share = None
    end_type = None
    filename = None
    username = None
    password = None
    mntpoint = None
    is_dir = False
    subdir = None
    recursive = False
    options = None

    _command = "mount.cifs"

    def __init__(self,end_type,server,share,username,password,is_dir,recursive,tempdir=j.dirs.tmpDir,Atype='copy'):
        """
        Initialize connection
        """
        self.logger = j.logger.get("j.sal.cloudfs.Cifs")
        self.logger.info('starting CIFS with %s' %share)
        self.is_dir     = is_dir
        self.is_mounted = False
        self.recursive  = recursive
        self.end_type   = end_type
        self.server     = server
        self.curdir     = os.path.realpath(os.curdir)
        self.Atype      = Atype
        self.share      = share

        lshare = share
        while lshare.startswith('/'):
            lshare = lshare.lstrip('/')
        while lshare.endswith('/'):
            lshare = lshare.rstrip('/')
        share_path = lshare.split('/')

        self.sharename = share_path[0]
        if len(share_path) > 1:
            subdirs = share_path[1:]
        else:
            subdirs=[]

        if not is_dir:
            self.filename = subdirs[-1]
            self.path_components = subdirs[:-1]
        else:
            self.filename = None
            self.path_components = subdirs

        self.username = re.escape(username)
        self.password = re.escape(password)
        self.mntpoint = '/'.join(['/mnt',j.data.idgenerator.generateGUID()])
        self.path     = '/'.join(self.path_components)

        print(('self.sharename:'       + str(self.sharename)))
        print(('self.path_components:' + str(self.path_components)))
        print(('self.path:'            + str(self.path)))

    def _connect(self, suppressErrors=False):
        j.sal.fs.createDir(self.mntpoint)

        # Mount sharename
        if self.username == None and self.password == None:
            command = '%s //%s/%s %s -o' % (self._command,self.server,self.sharename,self.mntpoint)
        else:
            command = '%s //%s/%s %s -o username=%s,password=%s' % (self._command,self.server,self.sharename,self.mntpoint,self.username,self.password)
        self.logger.info("CifsFS: executing command [%s]" % command)
        exitCode, output = j.sal.process.execute(command,die=True, outputToStdout=False)

        # create remote dir
        j.sal.fs.createDir(j.sal.fs.joinPaths(self.mntpoint, self.path))

        self.orgmntpoint = self.mntpoint
        self.mntpoint    = j.sal.fs.joinPaths(self.mntpoint, self.path)


    def exists(self):
        """
        Checks file or directory existance
        """

        self._connect()

        if self.subdir:
            path = j.sal.fs.joinPaths(self.mntpoint, self.subdir, self.filename)
        else:
            if self.is_dir:
                path = self.mntpoint
            else:
                path = j.sal.fs.joinPaths(self.mntpoint, self.filename)

        return j.sal.fs.exists(path)


    def upload(self,uploadPath):
        """
        Store file
        """
        self._connect()
        if self.Atype == "move":
            if self.is_dir:
                if self.recursive:
                    j.sal.fs.moveDir(uploadPath,self.mntpoint)
                else:
                # walk tree and move
                    for file in j.sal.fs.walk(uploadPath, recurse=0):
                        self.logger.info("FileFS: uploading directory -  Copying file [%s] to path [%s]" % (file,self.mntpoint))
                        j.sal.fs.moveFile(file,self.mntpoint)
            else:
                self.logger.info("CifsFS: uploading file - [%s] to [%s] filename [%s] (sub directory [%s])" % (uploadPath,self.mntpoint,self.filename,self.subdir))
                if self.subdir:
                    rfile = j.sal.fs.joinPaths(self.subdir, self.filename)
                    self.logger.info("CifsFS: moving to [%s]" % rfile)
                    j.sal.fs.moveFile(uploadPath,j.sal.fs.joinPaths(self.mntpoint,rfile))
                else:
                    j.sal.fs.moveFile(uploadPath,j.sal.fs.joinPaths(self.mntpoint,self.filename))
        else:
            if self.Atype == "copy":
                if self.is_dir:
                    if self.recursive:
                        j.sal.fs.copyDirTree(uploadPath,self.mntpoint, update=True)
                    else:
                    # walk tree and copy
                        for file in j.sal.fs.walk(uploadPath, recurse=0):
                            self.logger.info("FileFS: uploading directory -  Copying file [%s] to path [%s]" % (file,self.mntpoint))
                            j.sal.fs.copyFile(file,self.mntpoint)
                else:
                    self.logger.info("CifsFS: uploading file - [%s] to [%s] filename [%s] (sub directory [%s])" % (uploadPath,self.mntpoint,self.filename,self.subdir))
                    if self.subdir:
                        rfile = j.sal.fs.joinPaths(self.subdir, self.filename)
                        self.logger.info("CifsFS: moving to [%s]" % rfile)
                        j.sal.fs.copyFile(uploadPath,j.sal.fs.joinPaths(self.mntpoint,rfile))
                    else:
                        j.sal.fs.copyFile(uploadPath,j.sal.fs.joinPaths(self.mntpoint,self.filename))

    def download(self):
        """
        Download file
        """
        self._connect()
        if self.is_dir:
            if self.subdir:
                pathname = j.sal.fs.joinPaths(self.mntpoint,self.subdir,self.filename)
            else:
                pathname = self.mntpoint
            self.logger.info("CifsFS: downloading from [%s]" % pathname)
            return pathname
        else:
            if self.subdir:
                pathname =  j.sal.fs.joinPaths(self.mntpoint,self.subdir,self.filename)
            else:
                pathname =  j.sal.fs.joinPaths(self.mntpoint,self.filename)
            self.logger.info("CifsFS: downloading from [%s] the file [%s]" % (pathname,self.filename))
            return pathname

    def cleanup(self):
        """
        Umount cifs share
        """
        # umount the samba share
        self.logger.info("CifsFS: Cleaning up and umounting the share")
        command = "umount %s" % self.orgmntpoint

        exitCode, output = j.sal.process.execute(command, die=False, outputToStdout=False)
        if not exitCode == 0:
            raise j.exceptions.RuntimeError('Failed to execute command %s'%command)

        if j.sal.fs.exists(self.orgmntpoint):
            j.sal.fs.removeDir(self.orgmntpoint)

        self.is_mounted = False

    def list(self):
        """
        List content of directory
        """
        os.chdir(self.mntpoint)
        if self.path_components:
            if len(self.path_components) > 1:
                os.chdir('/'.join(self.path_components[:-1]))
                if os.path.isdir(self.path_components[-1]):
                    os.chdir(self.path_components[-1])
                else:
                    raise j.exceptions.RuntimeError('%s is not a valid directory under %s' %('/'.join(self.path_components),self.sharename))
            if os.path.isdir(self.path_components[0]):
                os.chdir(self.path_components[0])

        flist = j.sal.fs.walk(os.curdir,return_folders=1,return_files=1)
        os.chdir(self.curdir)
        self.logger.info("list: Returning content of share [%s] which is tmp mounted under [%s]" % (self.share , self.mntpoint))

        return flist

    def __del__(self):
        if self.is_mounted:
            self.logger.info('CifsFS GC')
            self.cleanup()
        os.chdir(self.curdir)
