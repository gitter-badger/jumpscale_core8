from JumpScale import j


from BackupClient import BackupClient

class BackupFactory:
    def __init__(self):
        self.__jslocation__ = "j.tools.backup_vfs"
        self.logger = j.logger.get("j.tools.backup_vfs")
        self._cache={}

    def get(self, backupname,blobstorAccount,blobstorNamespace,gitlabAccount,compress=True,fullcheck=False,servercheck=True,storpath="/mnt/STOR"):
        """
        @param backupdomain is domain used in blobstor
        """
        name="%s_%s_%s_%s"%(backupname,blobstorAccount,blobstorNamespace,gitlabAccount)
        if name in self._cache:
            return self._cache[name]
        self._cache[name]= BackupClient(backupname=backupname,blobstorAccount=blobstorAccount,blobstorNamespace=blobstorNamespace, \
            gitlabAccount=gitlabAccount,compress=compress,servercheck=servercheck,fullcheck=fullcheck,storpath=storpath)
        return self._cache[name]
