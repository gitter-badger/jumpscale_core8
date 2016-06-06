from JumpScale import j
from ftplib import FTP, error_perm
import os

# maybe this could be switched to http://curlftpfs.sourceforge.net/
class FtpFS:

    server = None
    path = None
    filename = None
    end_type = None
    username = 'anonymous'
    password = 'user@aserver.com'
    local_file = None
    ftp = None
    is_dir = False
    recursive = False

    def __init__(self,end_type,server,path,username,password,is_dir=False,recursive=False,tempdir=j.dirs.tmpDir, Atype='copy'):
        """
        Initialize connection
        """
        self.logger = j.logger.get('j.sal.cloudfs.FtpFS')
        self.logger.info("FtpFS: connection information: server [%s] path [%s] username [%s] password [%s]" % (server,path,username,password))

        self.end_type = end_type
        self.Atype = Atype
        self.server = server
        # what if no path is specified
        self.filename = j.sal.fs.getBaseName(path)
        #self.path = path.rstrip(self.filename).lstrip('/')
        self.path = os.path.dirname(path).lstrip('/')
        self.logger.info("FtpFS: path is %s" % self.path)
        self.local_dir =  j.sal.fs.joinPaths(tempdir , j.data.idgenerator.generateGUID())
        self.local_file = j.sal.fs.joinPaths(self.local_dir , self.filename)
        self.tempdir=tempdir
        j.sal.fs.createDir(self.local_dir)

        self.is_dir = is_dir
        self.recursive = recursive

        if is_dir == False:
            self.logger.info("FtpFS: copying filename [%s] path [%s]" % (self.filename,self.path))
        else:
            self.logger.info("FtpFS: copying to local directory [%s] from path [%s]" % (self.local_dir,self.path))

        self.username = username
        self.password = password

    def _connect(self, dontCD=False):
        try:
            self.ftp = FTP(self.server)
            #self.ftp.set_debuglevel(2)
            self.ftp.connect()
            self.ftp.set_pasv(True)
            if self.username != None and self.password != None:
                self.ftp.login(self.username,self.password)
            else:
                self.ftp.login()
        except:
            raise j.exceptions.RuntimeError('Failed to login on ftp server [%s] credentials login: [%s] pass [%s]' % (self.server,self.username,self.password))
        # change to correct directory
        if not dontCD:
            path = self.path.lstrip(os.sep).split(os.sep)
            for directory in path:
                try:
                    self.ftp.cwd(directory)
                except Exception as e:
                    self.ftp.mkd(directory)
                    self.ftp.cwd(directory)


    def exists(self):
        """
        Checks file or directory existance
        """

        self._connect(dontCD=True)

        try:
            self.ftp.cwd(self.path)

            if self.is_dir:
                return True
        except error_perm as error:
            if error.message.startswith('550'):
                return False
            else:
                raise error

        if not self.is_dir:
            try:
                self.ftp.sendcmd("MDTM %(fileName)s" % {'fileName': self.filename})
                return True
            except error_perm as error:
                if error.message.startswith('550'):
                    return False
                else:
                    raise error


    def upload(self,uploadPath):
        """
        Store file
        """
        self._connect()
        self.logger.info("FtpFS: uploading [%s] to FTP server" % uploadPath)
        if self.is_dir:
            f = j.sal.fs.listFilesInDir(uploadPath)
            f += j.sal.fs.listDirsInDir(uploadPath)
    #                d = j.sal.fs.listDirsInDir(uploadPath,self.recursive)
            for file in f:
                self.logger.info("Checking file [%s]" % file)
                if j.sal.fs.isDir(file):
                    self.handleUploadDir(file,uploadPath)
                else:
                    remotefile = j.sal.fs.getBaseName(file)
                    self.storeFile(remotefile,file)
        else:
            if j.sal.fs.getBaseName(self.local_file) == '':
                remotefile = j.sal.fs.getBaseName(uploadPath)
            else:
                remotefile = self.filename

            self.storeFile(remotefile,uploadPath)

    def download(self):
        """
        Download file
        """
        self._connect()
        # FIXME: make sure the original file name is kept
        # should return path to which file was downloaded
        if self.is_dir:
            self.logger.info("FtpFS: downloading dir [%s]" % self.path)
            listing = []
            remote_file_list = self.ftp.retrlines('LIST', listing.append)
            for l in listing:
                t = l.split()
                name = t[-1:]
                self.logger.info("Checking t [%s] with name [%s]" % (t,name))
                if len(name) > 0:
                    if t[0].startswith('d'): #WARNING: dirty-hack alarm!
                        ldir = j.sal.fs.joinPaths(self.ftp.pwd(), name[0])
                        self.handleDownloadDir(ldir)
                    elif t[0].startswith('l'):
                        self.logger.info("FtpFS: symlink on FTP (skipping)")
                    else: # it's a normal file
                        self.logger.info("FtpFS: normal file")
                        #rdir = '/'.join([self.local_dir , self.path])
                        rdir = j.sal.fs.joinPaths(self.local_dir , self.path)
                        j.sal.fs.createDir(rdir)
                        self.retrieveFile(name[0],self.path,rdir)
                else:
                    self.logger.info("FtpFS: skipping [%s]" % name)
            return self.local_dir
        else:
            self.retrieveFile(self.filename,self.path,self.local_file)
            return self.local_file

    def cleanup(self):
        """
        Cleanup of ftp connection
        """
        self.ftp.quit()
        j.sal.fs.removeDirTree(self.local_dir)

    def retrieveFile(self,file,dir,dest):
        """
        Ftp copying file
        """
        if self.is_dir:
            lfile = j.sal.fs.joinPaths(dest, file)
        else:
            lfile = self.local_file
        self.logger.info("FtpFS: retrieving [%s] from dir [%s] to [%s]" % (file, dir,lfile))
        self.ftp.retrbinary('RETR %s' % file, open(lfile, 'wb').write)

    def storeFile(self,file,uploadPath):
        """
        Ftp upload file
        """
        self.logger.info("FtpFS: storing [%s] from [%s]" % (file,uploadPath))
        # print "%s:%s:%s %s %s"%(self.server,self.username,self.password,file,uploadPath)
        self.ftp.storbinary('STOR %s' % file, open(uploadPath, 'rb'), 8192)
        size=self.ftp.size(file)
        stat=j.sal.fs.statPath(uploadPath)
        if size!=stat.st_size:
            self.ftp.delete(file)
            raise j.exceptions.RuntimeError("Could not upload:%s %s, size different, have now deleted"%(file,uploadPath))

    def handleUploadDir(self,dir,upload_path):
        """
        Ftp handle a upload directory
        """
        self._connect()
        self.logger.info("FtpFS: handleUploadDir [%s]" % dir)
        dname = j.sal.fs.getBaseName(dir)
        self.logger.info("FtpFS: dirname is %s and upload path %s" % (dname, upload_path))
        fname =  dir.replace(upload_path, '')
        previous_dir = '/'.join(['/' , self.path])
        #creating directory on FTP
        self.logger.info("FtpFS: mkd and cwd to [%s] (previous dir %s)" % (fname,previous_dir))
        self.ftp.mkd(fname)
        #self.ftp.cwd(fname)

        f = j.sal.fs.listFilesInDir(dir)
        f += j.sal.fs.listDirsInDir(dir)
#       d = j.sal.fs.listDirsInDir(uploadPath,self.recursive)
        for file in f:
            self.logger.info("Checking file [%s]" % file)
            if j.sal.fs.isDir(file):
                self.handleUploadDir(file,upload_path)
            else:
                remotefile = j.sal.fs.getBaseName(file)
                self.ftp.cwd(fname)
                self.storeFile(remotefile,file)
                self.ftp.cwd(previous_dir)

    def handleDownloadDir(self,dirname):
        """
        Ftp handle a download directory
        """
        self._connect()
        self.logger.info("FtpFS: handleDownloadDir [%s]" % dirname)
        rdir = '/'.join([self.local_dir , dirname])
        self.logger.info("FtpFs: handleDownloadDir - creating local [%s]" % rdir)
        j.sal.fs.createDir(rdir)
        self.ftp.cwd(dirname)

        listing = []
        remote_file_list = self.ftp.retrlines('LIST', listing.append)
        for l in listing:
            t = l.split()
            name = t[-1:]
            self.logger.info("Checking t [%s] with name [%s]" % (t,name))
            if len(name) > 0:
                if t[0].startswith('d'): #WARNING: dirty-hack alarm!
                    ldir = j.sal.fs.joinPaths(self.ftp.pwd(), name[0])
                    self.handleDownloadDir(ldir)
                elif t[0].startswith('l'):
                    self.logger.info("FtpFS: symlink on FTP (skipping)")
                else: # it's a normal file
                    self.logger.info("FtpFS: normal file, attempting to retrieve file [%s] to location [%s]" % (name[0], rdir))
                    self.retrieveFile(name[0],self.path,rdir)
            else:
                self.logger.info("FtpFS: skipping [%s]" % name)

        previous_dir = dirname.rstrip(j.sal.fs.getBaseName(dirname))
        self.ftp.cwd(previous_dir)

    def list(self):
        """
        List files in dir
        """
        self._connect()
        dir_content = []
        self.logger.info("list: Returning list of FTP directory [%s]" % self.path)
        listing = []
        self.ftp.retrlines('LIST', listing.append)
        for l in listing:
            t = l.split()
            name = t[-1:][0]
            dir_content.append(name)

        return dir_content
