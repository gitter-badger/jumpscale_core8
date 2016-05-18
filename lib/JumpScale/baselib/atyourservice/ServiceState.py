from JumpScale import j

from collections import OrderedDict

class ServiceState():
    def __init__(self, service):

        self.service = service

        self._path = j.sal.fs.joinPaths(self.service.path, "state.yaml")
        if j.sal.fs.exists(path=self._path):
            self._model=j.data.serializer.yaml.load(self._path)
        else:
            self._model={"parent":"","producers":{},"state":{},"recurring":{},"events":{},"templateHRDHash":"","instanceHRDHash":"","recipe":""}

        self._changed=False

    @property
    def methods(self):
        """
        return dict
            key = action name
            val = state
        state = INIT,ERROR,OK,DISABLED,DO,CHANGED,CHANGEDHRD  DO means: execute the action method as fast as you can, init means it has not been started yet ever

        """
        return self._model["state"]

    def set(self,name,state="DO"):
        """
        state = INIT,ERROR,OK,DISABLED,DO,CHANGED,CHANGEDHRD  DO means: execute the action method as fast as you can, init means it has not been started yet ever
        """
        if state not in ["INIT","ERROR","OK","DISABLED","DO","CHANGED","CHANGEDHRD"]:
            raise j.exceptions.Input("State needs to be in INIT,ERROR,OK,DISABLED,DO,CHANGED,CHANGEDHRD")
        name=name.lower()
        if name not in self._model["state"] or self._model["state"][name]!=state:
            self._model["state"][name]=state
            self.changed=True

    def getSet(self,name,default="DO"):
        """
        state = INIT,ERROR,OK,DISABLED,DO,CHANGED,CHANGEDHRD  DO means: execute the action method as fast as you can, init means it has not been started yet ever
        """
        name = name.lower()
        if default not in ["INIT","ERROR","OK","DISABLED","DO","CHANGED","CHANGEDHRD"]:
            raise j.exceptions.Input("State needs to be in INIT,ERROR,OK,DISABLED,DO,CHANGED,CHANGEDHRD")
        if name not in self._model["state"]:
            self._model["state"][name]=default
            self.changed=True
        else:
            return  self._model["state"][name]

    def get(self,name,die=True):
        name = name.lower()
        if name in self._model["state"]:
            return self._model["state"][name]
        else:
            if die:
                raise j.exceptions.Input("Cannot find state with name %s"%name)
            else:
                return None


    @property
    def changed(self):
        return self._changed

    @changed.setter
    def changed(self,changed):
        self._changed=changed

    @property
    def recipe(self):
        return self._model["recipe"]

    @recipe.setter
    def recipe(self,recipe):
        self._model["recipe"]=recipe
        self.changed=True

    @property
    def instanceHRDHash(self):
        return self._model["instanceHRDHash"]

    @instanceHRDHash.setter
    def instanceHRDHash(self,instanceHRDHash):
        self._model["instanceHRDHash"]=instanceHRDHash
        self.changed=True

    @property
    def templateHRDHash(self):
        return self._model["templateHRDHash"]

    @templateHRDHash.setter
    def templateHRDHash(self,templateHRDHash):
        self._model["templateHRDHash"]=templateHRDHash
        self.changed=True

    @property
    def recurring(self):
        """
        return dict
            key = action name
            val = (period,lastrun)

        lastrun = epoch
        period = e.g. 1h, 1d, ...
        """        
        return self._model["recurring"]

    def setRecurring(self, name, period):
        """
        """
        name=name.lower()
        if name not in self._model["recurring"] or self._model["recurring"][name][0]!=period:
            self._model["recurring"][name]=[period,0]
            self.changed=True

    @property
    def events(self):
        """
        return dict
            key = event name
            val = [actions]
        """        
        try:
            return self._model["events"]
        except KeyError:
            return {}

    def setEvents(self, event, actions):
        """
        """
        event = event.lower()
        change = False
        if event not in self._model["events"]:
            change = True
        else:
            if self._model["events"][event].sort() != actions.sort():
                change = True

        if change:
            self._model["events"][event] = actions
        self.changed = change

    def check(self):
        """
        walks over the recurring items and if too old will execute
        """
        from IPython import embed
        print ("DEBUG NOW check recurring")
        embed()

    @property
    def parent(self):
        return self._model["parent"]

    @parent.setter
    def parent(self,parent):
        #will check if service exists
        self.service.aysrepo.getServiceFromKey(parent)
        if self._model["parent"]!=parent:
            self._model["parent"]=parent
            self.consume(parent)
            self.changed=True
            self.service.reset()

    @property
    def producers(self):
        return self._model["producers"]


    def consume(self,producerkey="",aysi=None):
        """
        """
        #will check if service exists
        if aysi==None:
            aysi=self.service.aysrepo.getServiceFromKey(producerkey)
        if aysi.role not in  self._model["producers"]:
            self._model["producers"][aysi.role]=[]
            self.changed=True
        if aysi.key not in self._model["producers"][aysi.role]:
            self._model["producers"][aysi.role].append(aysi.key)
            self._model["producers"][aysi.role].sort()
            self.changed=True
            self.service.reset()

    @property
    def model(self):
        return self._model

    @property
    def wiki(self):

        out="## service:%s state"%self.service.key

        if self.parent!="":
            out+="\n- parent:%s\n\n"%self.parent

        if self.producers!={}:
            out = "### producers\n\n"
            out += "| %-20s | %-30s |\n" % ("role", "producer")
            out += "| %-20s | %-30s |\n" % ("---", "---")
            for role,producers in self.producers.items():
                for producer in producers:
                    out+= "| %-20s | %-30s |\n" % (role,producer)
            out +="\n"

        if self.recurring!={} or self.methods!={}:
            methods=OrderedDict()
            for actionname,actionstate in self.methods.items():
                methods[actionname]=[actionstate,"",0]
            for actionname,obj in self.recurring.items():
                period,last=obj
                actionstate,_,_=methods[actionname]
                methods[actionname]=[actionstate,period,int(last)]

            out = "### actions\n\n"
            out += "| %-20s | %-10s | %-10s | %-30s |\n" % ("name", "state","period", "last")
            out += "| %-20s | %-10s | %-10s | %-30s |\n" % ("---", "---","---", "---")
            for actionname, obj in methods.items():
                actionstate,period,last=obj
                out += "| %-20s | %-10s | %-10s | %-30s |\n" % (actionname,actionstate,period,last)
            out +="\n"

        return out

    def save(self):
        if self.changed:
            # self.service.logger.info ("State Changed, writen to disk.")
            j.data.serializer.yaml.dump(self._path,self.model)
            self.changed=False

    def __repr__(self):
        return str(self.wiki)

    def __str__(self):
        return self.__repr__()
