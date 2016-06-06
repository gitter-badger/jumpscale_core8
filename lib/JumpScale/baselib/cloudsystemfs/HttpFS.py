from JumpScale import j
# import urllib.request, urllib.error, urllib.parse

# try:
#     import urllib
# except:
#     import urllib.parse as urllib

import http.client

CHUNKSIZE=8192

# FIXME: HTTP basic authentication support
class HttpFS:

    server = None
    path = None
    filename = None
    local_file = None
    end_type = None
    local_file = None
    http_socket = None

    def __init__(self,end_type,server,path,tempdir=j.dirs.tmpDir,Atype=None):
        """
        Initialize connection
        """
        self.logger = j.logger.get('j.sal.cloudfs.HTTPFS')
        self.logger.info("HttpFS: connection information: server [%s] path [%s]" % (server,path))
        self.filename = j.sal.fs.getBaseName(path)
        self.tempdir=tempdir

        # Simple assumption
        if len(self.filename) == 0:
            self.filename = 'index.html'
            self.path = 'index.html'
        else:
            self.path = path

        """
        Initialize connection
        """
        self.logger.info("HttpFS: connection information: server [%s] path [%s]" % (server,path))
        self.filename = j.sal.fs.getBaseName(path)
        self.tempdir=tempdir

        # Simple assumption
        if len(self.filename) == 0:
            self.filename = 'index.html'
            self.path = 'index.html'
        else:
            self.path = path

        self.server = server

    def _connect(self, suppressErrors=False):
        if not hasattr(self, 'local_dir') or not self.local_dir: self.local_dir =  '/'.join([self.tempdir , j.data.idgenerator.generateGUID()])
        self.local_file = '/'.join([self.local_dir , self.filename])
        self.local_dir = self.local_dir.replace('//', '/')
        self.local_file = self.local_file.replace('//', '/')

        # construct url again
        connect_url = 'http://%s%s' % (self.server,self.path)
        try:
            self.http_socket = urllib.request.urlopen(connect_url)
        except (urllib.error.HTTPError, http.client.HTTPException) as error:
            if suppressErrors:
                return False
            raise error

        return True

    def exists(self):
        """
        Checks if a file exists
        """
        try:
            self._connect(suppressErrors=False)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            else:
                raise

        return True

    def upload(self):
        """
        Upload of file
        This is currently not supported for HTTP
        """
        self._connect()
        return None

    def download(self):
        """
        Download file
        """
        self._connect()
        j.sal.fs.createDir(self.local_dir)
        self.logger.info("HttpFS: downloading file to local file [%s]" % self.local_file)
        file = open(self.local_file,'wb')
        rb = self.http_socket.read(CHUNKSIZE)
        while rb:
            file.write(rb)
            rb = self.http_socket.read(CHUNKSIZE)
        #file.write(self.http_socket.read(CHUNKSIZE))
        file.close()
        return self.local_file

    def cleanup(self):
        """
        Cleanup http connection and temp file
        """
        j.sal.fs.removeDirTree(self.local_dir)
