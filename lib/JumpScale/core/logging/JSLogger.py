from JumpScale import j
import sys
import logging
from Colors import LoggingColorizer

class JSLogger(logging.Logger):

    def __init__(self, name):
        super(JSLogger, self).__init__(name)
        self.custom_filters = {}
        self.__only_me = False
        self.colorizer = LoggingColorizer("default", False)

    def error_tb(self, ttype=None, exceptionObject=None, tb=None):
        if self.isEnabledFor(logging.ERROR):
            if (ttype, exceptionObject, tb) == (None, None, None):
                ttype, exceptionObject, tb = sys.exc_info()
            colored_tb = self.colorizer.colorize_traceback(ttype, exceptionObject, tb)
            self._log(logging.ERROR, colored_tb, ())

    def enable_only_me(self):
        """
        Enable filtering. Output only log from this logger and its children.
        Logs from other modules are masked
        """
        if not self.__only_me and 'console' in j.logger.handlers:
            only_me_filter = logging.Filter(self.name)
            j.logger.handlers['console'].addFilter(only_me_filter)
            self.custom_filters["only_me"] = only_me_filter
            self.__only_me = True

    def disable_only_me(self):
        """
        Disable filtering on only this logger
        """
        if self.__only_me and 'console' in j.logger.handlers:
            j.logger.handlers['console'].removeFilter(self.custom_filters['only_me'])
            self.__only_me = False
