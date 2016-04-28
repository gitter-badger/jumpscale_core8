from colored_traceback import Colorizer
from JumpScale import j

class StreamHepler():

    def __init__(self):
        self.logger = j.logger.get()

    def write(self, *args, **kwargs):
        return self.logger.error(*args, **kwargs)

class LoggingColorizer(Colorizer):

    @property
    def stream(self):
        return StreamHepler()
