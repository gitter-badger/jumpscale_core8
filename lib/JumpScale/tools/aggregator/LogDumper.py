from JumpScale import j

import time

#@TODO very early spec, needs to be done todo (*3*) despiegk

class LogDumper():
    """
    dump the info to log files, 
    for log's the log files are human readable
    for the other objects they are stored as json objects in a tar
    python has good support for tar
    name of file = key
    name of directory = j.data.time.getHourId(time) means we group per hour of object which came in 
    use first letter of key as subdir (otherwise tar becomes too heavy)
    """

    def __init__(self):


    def processLog(self,...):
        """
        recieve log from MongoDumper
        """