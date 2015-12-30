
from JumpScale import j

descr = """
remove old logs from system
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "log.cleanup"
period = 7200  # always in sec
startatboot = True
order = 1
enable = True
async = True
log = False



def action():
    
    for path in j.sal.fs.listFilesInDir( path=j.dirs.logDir, recursive=True,  minmtime=None, maxmtime=j.data.time.getEpochAgo("-3d"), followSymlinks=True):
        j.sal.fs.remove(path)

    

