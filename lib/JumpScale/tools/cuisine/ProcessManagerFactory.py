
from CuisineProcessManager import CuisineRunit, CuisineTmuxec, CuisineSystemd
from JumpScale import j

class ProcessManagerFactory:

    def __init__(self, cuisine):
        self.pms = {}
        self.cuisine = cuisine

    def systemdOK(self):
        return not self.cuisine.core.isDocker and self.cuisine.core.command_check("systemctl")

    def svOK(self):
        return self.cuisine.core.command_check("sv")

    def get_prefered(self):
        for pm in ["systemd", "sv", "tmux"]:
            if self.is_available( pm):
                return pm
    
    def is_available(self, pm):
        if pm == "systemd":
            return self.systemdOK()
        elif pm == "sv":
            return self.svOK()
        elif pm == "tmux":
            return True
        else:
            return False

    def get(self, pm = None):
        if pm == None:
            pm = self.get_prefered()
        else:
            if not self.is_available(pm):
                raise j.exceptions.OPERATIONS('%s processmanager is not available on your system'%(pm))

        if pm not in self.pms:
            if pm == "systemd":
                inst = CuisineSystemd(self.cuisine.core.executor, self.cuisine)
            elif pm == "sv":
                inst = CuisineRunit(self.cuisine.core.executor, self.cuisine)
            elif pm == "tmux":
                inst = CuisineTmuxec(self.cuisine.core.executor, self.cuisine)
            self.pms[pm] = inst

        return self.pms[pm]
