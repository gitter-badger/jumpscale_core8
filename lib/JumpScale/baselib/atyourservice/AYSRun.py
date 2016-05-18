from JumpScale import j

class AYSRunStep:

    def __init__(self,run,nr,action):
        """
        """
        self.run=run
        self.nr=nr
        self.services=[]
        self.serviceKeys={}
        self.action=action

    def addService(self,aysi):
        if aysi.key not in self.serviceKeys:
            self.services.append(aysi)
            self.serviceKeys[aysi.key]=aysi


    def exists(self,aysi):
        return aysi.key in self.serviceKeys

    def execute(self):
        for service in self.services:
            service.runAction(self.action)

    def __repr__(self):
        out=""
        for service in self.services:
            out+="- %-50s ! %-15s %s \n"%(service,self.action,service.state.get(self.action,die=False))
        return out

    __str__=__repr__

        


class AYSRun:

    def __init__(self,aysrepo):
        """
        """
        self.aysrepo=aysrepo
        self.steps=[]
        self.lastnr=0

    def exists(self,aysi,action):
        for step in self.steps:
            if step.action!=action:
                continue
            if step.exists(aysi):
                return True
        return False

    def newStep(self,action):
        self.lastnr+=1
        step=AYSRunStep(self,self.lastnr,action)
        self.steps.append(step)
        return step

    def sort(self):
        for step in self.steps:
            keys=[]
            items={}
            res=[]
            for service in step.services:
                items[service.key]=service
                keys.append(service.key)
            keys.sort()
            for key in keys:
                res.append(items[key])
            step.services=res

    @property
    def services(self):
        res=[]
        for step in self.steps:
            for service in step.services:
                res.append(service)
        return res

    @property
    def action_services(self):
        res=[]
        for step in self.steps:
            for service in step.services:
                res.append((step.action,service))
        return res

    def execute(self):
        for step in self.steps:
            step.execute()

    def __repr__(self):
        out=""
        for step in self.steps:
            out+="## step:%s\n\n"%step.nr
            out+="%s\n"%step
        return out

    __str__=__repr__
