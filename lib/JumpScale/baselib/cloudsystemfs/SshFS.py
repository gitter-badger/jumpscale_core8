import os
from JumpScale import j
import re

# requires sshfs package
class SshFS:

    server = None
    directory = None
    share = None
    filename = None
    end_type = None
    username = None
    password = None
    mntpoint = None
    _command = 'sshfs'

    def __init__(self,end_type,server,directory,username,password,is_dir,recursive,tempdir=j.dirs.tmpDir, Atype='copy'):
        """
        Initialize connection
        """
        self.logger = j.logger.get('j.sal.cloudfs.Cifs')
        self.is_dir = is_dir
        self.recursive = recursive
        self.end_type = end_type
        self.server = server
        self.share = directory
        self.tempdir=tempdir
        self.Atype = Atype
        self.curdir = os.path.realpath(os.curdir)

        ldirectory = directory
        while ldirectory.startswith('/'):
            ldirectory = ldirectory.lstrip('/')
        while ldirectory.endswith('/'):
            ldirectory = ldirectory.rstrip('/')
        self.path_components = ldirectory.split('/')


        if not self.is_dir:
            self.filename = j.sal.fs.getBaseName(directory)
            self.directory = os.path.dirname(self.share)
        else:
            self.directory = self.share

        self.username = re.escape(username)
        self.password = re.escape(password)
        self.mntpoint = '/'.join(['/mnt',j.data.idgenerator.generateGUID()])
        self.is_mounted = False


    def _connect(self):
        j.sal.fs.createDir(self.mntpoint)

        self.logger.info("SshFS: mounting share [%s] from server [%s] with credentials login [%s] and password [%s]" % (self.directory,self.server,self.username,self.password))

        command = "echo \"%s\" | %s %s@%s:%s %s  -o password_stdin -o StrictHostKeyChecking=no" % (self.password,self._command,self.username,self.server,self.directory,self.mntpoint)

        self.logger.info("SshFS: executing command [%s]" % command)

        exitCode, output = j.sal.process.execute(command,die=False, outputToStdout=False)
        if not exitCode == 0:
            raise j.exceptions.RuntimeError('Failed to execute command %s'%command)
        else:
            self.is_mounted = True


    def exists(self):
        """
        Checks file or directory existance
        """

        self._connect()

        if self.is_dir:
            path = self.mntpoint
        else:
            path = j.sal.fs.joinPaths(self.mntpoint, self.filename)

        return j.sal.fs.exists(path)


    def upload(self,uploadPath):
        """
        Store file
        """
        self. _connect()
        if self.Atype == "move":
            if self.is_dir:
                if self.recursive:
                    j.sal.fs.moveDir(uploadPath,self.mntpoint)
                else:
                    # walk tree and move
                    for file in j.sal.fs.walk(uploadPath, recurse=0):
                        self.logger.info("SshFS: uploading directory -  Copying file [%s] to path [%s]" % (file,self.mntpoint))
                        j.sal.fs.moveFile(file,self.mntpoint)
            else:
                self.logger.info("SshFS: uploading file - [%s] to [%s]" % (uploadPath,self.mntpoint))
                j.sal.fs.moveFile(uploadPath,j.sal.fs.joinPaths(self.mntpoint,self.filename))
        else:
            if self.Atype == "copy":
                if self.is_dir:
                    if self.recursive:
                        j.sal.fs.copyDirTree(uploadPath,self.mntpoint, update=True)
                    else:
                    # walk tree and copy
                        for file in j.sal.fs.walk(uploadPath, recurse=0):
                            self.logger.info("SshFS: uploading directory -  Copying file [%s] to path [%s]" % (file,self.mntpoint))
                            j.sal.fs.copyFile(file,self.mntpoint)
                else:
                    self.logger.info("SshFS: uploading file - [%s] to [%s]" % (uploadPath,self.mntpoint))
                    j.sal.fs.copyFile(uploadPath,j.sal.fs.joinPaths(self.mntpoint,self.filename))

    def download(self):
        """
        Download file
        """
        self. _connect()
        if self.is_dir:
            self.logger.info("SshFS: downloading from [%s]" % self.mntpoint)
            return self.mntpoint
        else:
            pathname =  j.sal.fs.joinPaths(self.mntpoint,self.filename)
            self.logger.info("SshFS: downloading from [%s]" % pathname)
            return pathname

    def cleanup(self):
        """
        Umount sshfs share
        """
        self.logger.info("SshFS: cleaning up and umounting share")
        command = "umount %s" % self.mntpoint

        exitCode, output = j.sal.process.execute(command,die=False, outputToStdout=False)
        if not exitCode == 0:
            raise j.exceptions.RuntimeError('Failed to execute command %s'%command)

        j.sal.fs.removeDir(self.mntpoint)
        self.is_mounted = False

    def list(self):
        """
        List content of directory
        """
        self._connect()
        os.chdir(self.mntpoint)
        if self.path_components:
            if len(self.path_components) > 1:
                os.chdir('/' + '/'.join(self.path_components[:-1]))
                if os.path.isdir(self.path_components[-1]):
                    os.chdir(self.path_components[-1])
                else:
                    raise j.exceptions.RuntimeError('%s is not a valid directory under %s' %('/'.join(self.path_components),self.sharename))
            if os.path.isdir(self.path_components[0]):
                os.chdir(self.path_components[0])

        flist = j.sal.fs.walk(os.curdir,return_folders=1,return_files=1)
        os.chdir(self.curdir)
        self.logger.info("list: Returning content of SSH Mount [%s] which is tmp mounted under [%s]" % (self.share , self.mntpoint))

        return flist
    def __del__(self):
        if self.is_mounted:
            self.logger.info('SshFS GC')
            self.cleanup()
        os.chdir(self.curdir)
