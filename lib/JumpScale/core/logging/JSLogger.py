from JumpScale import j
import logging

class JSLogger(logging.Logger):

    def __init__(self, name):
        super(JSLogger, self).__init__(name)
        self.custom_filters = {}
        self.__only_me = False

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
