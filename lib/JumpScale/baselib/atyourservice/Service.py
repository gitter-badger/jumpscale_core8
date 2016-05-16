from JumpScale import j
# import JumpScale.baselib.actions

# import pytoml
from contextlib import redirect_stdout
import io
import imp
import sys
from Recurring import Recurring
from ServiceState import ServiceState
# from ServiceRecipe import ServiceRecipe

# def log(msg, level=2):
#     j.logger.log(msg, level=level, category='AYS')

def loadmodule(name, path):
    parentname = ".".join(name.split(".")[:-1])
    sys.modules[parentname] = __package__
    mod = imp.load_source(name, path)
    return mod

def getProcessDicts(service, args={}):
    counter = 0

    defaults = {"prio": 10, "timeout_start": 10,
                "timeout_start": 10, "startupmanager": "tmux"}
    musthave = ["cmd", "args", "prio", "env", "cwd", "timeout_start",
                "timeout_start", "ports", "startupmanager", "filterstr", "name", "user"]

    procs = service.recipe.hrd.getListFromPrefixEachItemDict("process", musthave=musthave, defaults=defaults, aredict=[
                                                   'env'], arelist=["ports"], areint=["prio", "timeout_start", "timeout_start"])
    for process in procs:
        counter += 1

        process["test"] = 1

        if "name" not in process or process["name"].strip() == "":
            process["name"] = "%s_%s" % (service.name, service.instance)

        if service.recipe.hrd.exists("env.process.%s" % counter):
            process["env"] = service.recipe.hrd.getDict("env.process.%s" % counter)

        if not isinstance(process["env"], dict):
            raise j.exceptions.RuntimeError("process env needs to be dict")

    return procs


class Service:

    def __init__(self, servicerecipe=None,instance=None, path="", args=None, parent=None, originator=None):
        """
        @param consume is in format $role!$instance,$role2!$instance2
        """
        self.originator = originator
        self.logger = j.logger.get('j.atyourservice.service')

        if path!="" and j.sal.fs.exists(path):
            self.role,self.instance=j.sal.fs.getBaseName(path).split("!")
            self._name=None
            self._version=None
            self._domain=None
            self._recipe=None
            self._rememberActions = True
        else:
            # if not isinstance(servicerecipe,ServiceRecipe):
            #     raise j.exceptions.Input("pass Service Recipe Object.")

            if not j.data.types.string.check(instance) or instance=="":
                raise j.exceptions.Input("Instance needs to be a string.")

            if not j.data.types.string.check(path) or path=="":
                raise j.exceptions.Input("path needs to be specified of service, cannot be empty and needs to be string.")

            if j.data.types.string.check(servicerecipe):
                raise j.exceptions.RuntimeError("no longer supported, pass servicerecipe")

            if servicerecipe==None:
                raise j.exceptions.RuntimeError("service recipe cannot be None if path not specified")

            if instance==None:
                raise j.exceptions.RuntimeError("instance needs to be specified")


            self._name = servicerecipe.name.lower()
            self.instance=instance
            self._version = servicerecipe.template.version
            self._domain = servicerecipe.template.domain.lower()
            self._recipe = servicerecipe
            self.role = self.name.split(".")[0]
            self._rememberActions = False

        self.instance = self.instance.lower()

        self._parent = ""
        self._parentChain = None
        if parent is not None:
            self.path = j.sal.fs.joinPaths(parent.path,"%s!%s"%(self.role,self.instance))
            self._parent = parent.key

        self.path = path.rstrip("/")

        self._hrd = None
        self._hrd_hash = None
        self._yaml = None
        self._mongoModel = None

        self._action_methods = None
        self._action_methods_node = None

        self._dnsNames = []

        self.args = args or {}
        self._producers = {}
        self.cmd = None
        self._logPath = None

        if self.path == "" or self.path is None:
            raise j.exceptions.RuntimeError("cannot be empty")

        self._init = False

        self._state = None

        self._executor = None


    @property
    def key(self):
        return j.atyourservice.getKey(self)

    # @property
    # def key(self):
    #     return "%s!%s"%(self.role,self.instance)


    @property
    def name(self):
        if self._name is None:
            self._name=self.hrd.get("service.name")
        return self._name

    @property
    def version(self):
        if self._version is None:
            self._version=self.hrd.get("service.version")
        return self._version

    @property
    def domain(self):
        if self._domain is None:
            self._domain=self.hrd.get("service.domain")
        return self._domain

    @property
    def recipe(self):
        if self._recipe is None:
            self._recipe=j.atyourservice.getRecipe(domain=self.domain, name=self.name, version=self.version)
        return self._recipe

    @property
    def dnsNames(self):
        if self._dnsNames == []:
            self._dnsNames = self.hrd.getList("dns")
        return self._dnsNames

    @property
    def parents(self):
        if self._parentChain ==None:
            chain = []
            parent = self.parent
            while parent is not None:
                chain.append(parent)
                parent = parent.parent
            self._parentChain = chain
        return self._parentChain

    @property
    def parent(self):
        if isinstance(self._parent, str):
            # print ("parent cache miss")
            if self._hrd is not None and self.hrd.exists("parent"):
                role, instance = self.hrd.get("parent").split("!")
                instance = instance.split('@')[0]
                self._parent = j.atyourservice.getService(role, instance)
            else:
                self._parent=None
        return self._parent



    @property
    def hrd(self):
        if self._hrd is None:
            hrdpath = j.sal.fs.joinPaths(self.path, "instance.hrd")
            self._hrd = j.data.hrd.get(hrdpath, prefixWithName=False)
        return self._hrd


    @property
    def hrdhash(self):
        self.hrd.save()
        return j.data.hash.md5_string(str(self.hrd))

    @property
    def yaml(self):
        if self._yaml is None:
            path = j.sal.fs.joinPaths(self.path, "model.yaml")
            if j.sal.fs.exists(path):
                self._yaml = j.data.serializer.yaml.load(path)
        return self._yaml

    @property
    def mongoModel(self):
        if self._mongoModel is None:
            self._mongoModel = self.recipe.model
            if self.yaml:
                for k, v in self.yaml.items():
                    if k in self._mongoModel:
                        self._mongoModel[k] = v
        return self._mongoModel

    @property
    def state(self):
        if self._state==None:
            self._state=ServiceState(self)
        return self._state

    @property
    def actions(self):
        if self._action_methods is None:
            print ("reload mgmt actions for %s"%(self))
            action_methods = self._loadActions(self.recipe.path_actions,"mgmt")
            self._action_methods = action_methods
        return self._action_methods


    # @property
    # def action_methods_node(self):
    #     if self._action_methods_node is None or not self._rememberActions:
    #         if j.sal.fs.exists(path=self.recipe.path_actions_node):
    #             action_methods_node = self._loadActions(self.recipe.path_actions_node,"node")
    #         else:
    #             action_methods_node = j.atyourservice.getActionsBaseClassNode()()

    #         self._action_methods_node=action_methods_node

    #     return self._action_methods_node


    # def getAction(self, name, printonly=False):
    #     if name not in self._actionlog:
    #         action = self._setAction(name, printonly=printonly)
    #         print("new action:%s (get)" % action)
    #     else:
    #         action=self._actionlog[name]
    #     action.printonly = printonly
    #     self.action_current = action
    #     return action

    # def runAction(self,name,printonly=False):
    #     """
    #     look for action & run, there are no arguments
    #     """
    #     method=self._getActionMethodMgmt(name)
    #     if method==None:
    #         return None
    #     action=j.actions.add(method, kwargs={"ayskey":self.key}, die=True, stdOutput=False, \
    #             errorOutput=False, executeNow=True,force=True, showout=False, actionshow=True,selfGeneratorCode='selfobj=None')
    #     from IPython import embed
    #     print ("DEBUG NOW runaction")
    #     embed()

    #     return action

    # def runActionNode(self,name,*args,**kwargs):
    #     """
    #     run on node, need to pass all arguments required
    #     there are no arguments given by default
    #     """
    #     method=self._getActionMethodNode(name)
    #     if method==None:
    #         return None
    #     from IPython import embed
    #     print ("DEBUG NOW runaction node")
    #     embed()
    #     return action

    def _getActionMethodMgmt(self,action):
        try:
            method=eval("self.action_methods_mgmt.%s"%action)
        except Exception as e:
            if str(e).find("has no attribute")!=-1:
                return None
            raise j.exceptions.RuntimeError(e)
        return method

    def _getActionMethodNode(self,action):
        try:
            method=eval("self.action_methods_node.%s"%action)
        except Exception as e:
            if str(e).find("has no attribute")!=-1:
                return None
            raise j.exceptions.RuntimeError(e)
        return method

    def _loadActions(self, path,ttype):
        self.cleanOnRepo()
        if j.sal.fs.exists(path):
            j.sal.fs.createDir(j.sal.fs.getDirName(path))
            path2 = j.sal.fs.joinPaths(self.path, j.sal.fs.getBaseName(path))
            # need to create a copy of the recipe mgmt or node action class
            j.sal.fs.copyFile(path, path2)
            if self.hrd is not None:
                self.hrd.applyOnFile(path2)
            j.application.config.applyOnFile(path2)
        else:
            j.events.opserror_critical(msg="can't find %s." % path, category="ays loadActions")

        modulename = "JumpScale.atyourservice.%s.%s.%s.%s" % (self.domain, self.name, self.instance, ttype)
        mod = loadmodule(modulename, path2)
        #is only there temporary don't want to keep it there

        actions = mod.Actions()

        # if 'roletemplate' in super(actions.__class__, actions).__module__:
        #     hrd = j.atyourservice.getRoleTemplateHRD(self.role)
        #     if hrd and self._hrd:
        #         for key in hrd.items.keys():
        #             if not self._hrd.exists(key):
        #                 self._hrd.set(key, hrd.get(key))

        return actions

    def cleanOnRepo(self):
        j.sal.fs.removeDirTree(j.do.joinPaths(self.path,"__pycache__"))
        # j.sal.fs.remove(j.sal.fs.joinPaths(self.path, "actions.py"))

    @property
    def producers(self):
        if self._producers is None or self._producers == {}:
            self._producers={}
            for key, items in self.hrd.getDictFromPrefix("producer").items():
                producerSet = set()
                for item in items:
                    domain, _, _, instance, role = j.atyourservice.parseKey(item)
                    service = j.atyourservice.getService(role=role, instance=instance)
                    producerSet.add(service)

                self._producers[key] = list(producerSet)

            if self.parent is not None:
                self._producers[self.parent.role]=[self.parent]

        return self._producers

    @property
    def executor(self):
        if self._executor is None:
            self._executor = self._getExecutor()
        return self._executor

    def save(self):
        self.state.save()

    def init(self, yaml=None):
        def _initParent():
            parent = self.recipe.schema.parentSchemaItemGet()

            if parent != None:
                # parent exists
                name = parent.parent
                role = name

                if '.' in name:
                    role = name.split('.', 1)[0]

                #parent.name is name of element in scheme which points to item we are filling in
                if parent.name in self.args:
                    # has been speficied or empty
                    instance = self.args[parent.name].strip()
                else:
                    instance = ""

                if role == name:
                    ays_s = j.atyourservice.findServices(role=role, instance=instance)
                else:
                    ays_s = j.atyourservice.findServices(name=name, instance=instance)

                if len(ays_s) == 1:
                    # we found 1 service of required role, will take that one
                    aysi = ays_s[0]
                    rolearg = aysi.instance
                    self.args[role] = rolearg
                elif len(ays_s) > 1:
                    raise j.exceptions.Input("Found more than one parent candidate with role '%s' for service '%s'" % (role, self))
                else:
                    if parent.auto:
                        ays_s = [j.atyourservice.new(name=parent.parent, instance='main', version='', domain='', path=None, parent=None, args={}, consume='')]
                        rolearg = "main"
                    else:
                        if instance!="":
                            raise j.exceptions.Input("Cannot find parent '%s!%s' for service '%s, there is none, please make sure the service exists."%(role,instance, self))
                        else:
                            raise j.exceptions.Input("Cannot find parent with role '%s' for service '%s, there is none, please make sure the service exists."%(role, self))

                self._parent = ays_s[0]
                self.path = j.sal.fs.joinPaths(self.parent.path,"%s!%s"%(self.role,self.instance))

        if self._init is False:
            self.logger.info('INIT service: %s' % self)

            self._hrd_hash = None

            # make sure yaml is written again, which means changes will be detected
            if yaml is not None:
                yamlpath = j.sal.fs.joinPaths(self.path, "model.yaml")
                if not j.sal.fs.exists(yamlpath):
                    j.sal.fs.touch(yamlpath)
                j.data.serializer.yaml.dump(yamlpath, yaml)

            # see if we can find parent if specified (potentially based on role)
            if not self.parent:
                _initParent()  #@question what exactly does this thing do & why (despiegk)

            j.sal.fs.createDir(self.path)

            # run the args manipulation action as an action
            self.args = self.actions.input(self.name, self.role, self.instance, self.args)

            hrdpath = j.sal.fs.joinPaths(self.path, "instance.hrd")

            # self._manipulateArgs()
            self._hrd = self.recipe.schema.hrdGet(hrd=self.hrd, args=self.args, path=hrdpath)
            self._hrd.save()

            if self.recipe.hrd is not None:
                #apply values from recipe hrd to this hrd
                self.hrd.applyTemplate(self.recipe.hrd)

            self.hrd.prefixWithName = False
            self.hrd.set("service.name", self.name)
            self.hrd.set("service.version", self.version)
            self.hrd.set("service.domain", self.domain)
            self.hrd.set("service.role", self.role)
            self.hrd.set("service.instance", self.instance)

            if self.parent is not None:
                self.hrd.set("parent", self.parent.key)
                self.consume(self.parent)

            self._consumeFromSchema()

            self._action_methods = None  # to make sure we reload the actions

            self.actions.init()

            for item in self.hrd.prefix("recurring"):
                recurringName = item.split(".")[1]
                recurringPeriod = self.hrd.getStr(item).strip("\"")
                self.state.addRecurring(recurringName, recurringPeriod)

            self._hrd.save()

            for key, _ in self.recipe.actionmethods.items():
                stateitem=self.state.getSet(key)

                if stateitem.state=="OK":
                    #lets check if we don't have to put it on changed depending the method changes
                    if stateitem.actionObj.hash!=stateitem.actionmethod_hash:
                        stateitem.state="CHANGED"
                        self.state.save()
                        self.actions.change(stateitem)

                    if self.hrdhash!=stateitem.hrd_hash:
                        stateitem.state="CHANGEDHRD"
                        self.state.save()
                        self.actions.change(stateitem)

            self.state.save()
            self.cleanOnRepo()

        self._init = True

    # def _manipulateArgs(self):

    #     def exists(args, name):
    #         x = name not in args or args[name] is None or args[name] == ""
    #         return not x

    #     ##fill in node.tcp.address
    #     if self.name.startswith("node"):
    #         # set service name & ip addr
    #         if not exists(self.args, 'node.tcp.addr') or self.args['node.tcp.addr'].find('@ask')!=-1:
    #             if "ip" in self.args:
    #                 self.args['node.tcp.addr'] = self.args["ip"]

    #         if not exists(self.args, 'node.name'):
    #             self.args['node.name'] = self.instance

    def _consumeFromSchema(self):
        #manipulate the HRD's to mention the consume's to producers
        consumes = self.recipe.schema.consumeSchemaItemsGet()

        if consumes:
            for consumeitem in consumes:
                #parent exists
                role = consumeitem.consume_link
                consumename = consumeitem.name

                if role in self.producers:
                    continue

                instancenames = []
                if consumename in self.args:
                    instancenames = self.args[consumename]

                ays_s = list()
                candidates = j.atyourservice.findServices(role=consumeitem.consume_link)
                if len(candidates)>0:
                    if len(instancenames)>0:
                        ays_s = [candidate for candidate in candidates if candidate.instance in instancenames]
                    else:
                        ays_s = candidates

                # autoconsume
                if len(candidates) < int(consumeitem.consume_nr_min) and consumeitem.auto:
                    for instance in range(len(candidates), int(consumeitem.consume_nr_min)):
                        consumable = j.atyourservice.new(name=consumeitem.consume_link, instance='auto_%i' % instance, parent=self.parent)
                        ays_s.append(consumable)

                if len(ays_s) > int(consumeitem.consume_nr_max):
                    raise j.exceptions.RuntimeError("Found too many services with role '%s' which we are relying upon for service '%s, max:'%s'" % (role, self, consumeitem.consume_nr_max))
                if len(ays_s) < int(consumeitem.consume_nr_min):
                    msg = "Found not enough services with role '%s' which we are relying upon for service '%s, min:'%s'" % (role, self, consumeitem.consume_nr_min)
                    if len(ays_s) > 0:
                        msg += "Require following instances:%s" % self.args[consumename]
                    raise j.exceptions.RuntimeError(msg)

                for ays in ays_s:
                    if role not in self.producers:
                        self._producers[role] = []
                    if ays not in self._producers[role]:
                        self._producers[role].append(ays)

            for key,producers in self.producers.items():
                producers=[item.key for item in producers]
                producers.sort()
                self.hrd.set("producer.%s"%key,producers)


    def consume(self, input):
        """
        @input is comma separate list of ayskeys or a Service object or list of Service object

        ayskeys in format $domain|$name:$instance@role ($version)

        example
        ```
        @input $domain|$name!$instance,$name2!$instance2,$name2,$role4
        ```

        """
        print ("input:'%s'"%input)
        if input is not None and input is not '':
            toConsume = set()
            if j.data.types.string.check(input):
                entities = [item for item in input.split(",") if item.strip()!=""]
                for entry in entities:
                    service = j.atyourservice.getServiceFromKey(entry.strip())
                    toConsume.add(service)

            elif j.data.types.list.check(input):
                for service in input:
                    toConsume.add(service)

            elif isinstance(input, Service):
                toConsume.add(input)
            else:
                raise j.exceptions.Input("Type of input to consume not valid. Only support list, string or Service object", category='AYS.consume', msgpub='Type of input to consume not valid. Only support list, string or Service object')

            for service in toConsume:
                if service.role not in self._producers:
                    self._producers[service.role] = [service]
                else:
                    prodSet = set(self._producers[service.role])
                    prodSet.add(service)
                    self._producers[service.role] = list(prodSet)

            for role, services in self._producers.items():
                producers = set()
                for service in services:
                    producers.add(service.key)
                list_prods = list(producers)
                list_prods.sort()
                self.hrd.set("producer.%s" % role, list_prods)


            # # walk over the producers
            # # for producer in toConsume:
            # method = self._getActionMethodMgmt("consume")
            # if method:
            #     self.runAction('consume')

    def getProducersRecursive(self, producers=set(), callers=set()):
        for role, producers2 in self.producers.items():
            for producer in producers2:
                producers.add(producer)
                producers = producer.getProducersRecursive(producers, callers=callers)
        return producers.symmetric_difference(callers)

    def printProducersRecursive(self,prefix=""):
        for role, producers2 in self.producers.items():
            # print ("%s%s"%(prefix,role))
            for producer in producers2:
                print ("%s- %s"%(prefix,producer))
                producer.printProducersRecursive(prefix+"  ")


    def getProducersWaiting(self, action="install",producersChanged=set(),scope=None):
        """
        return list of producers which are waiting to be executing the action
        """

        # print ("producerswaiting:%s"%self)
        for producer in self.getProducersRecursive(set(), set()):
            #check that the action exists, no need to wait for other actions, appart from when init or install not done
            
            if producer.state.getSet("init").state!= "OK":
                producersChanged.add(producer)

            if producer.state.getSet("install").state!= "OK":
                producersChanged.add(producer)

            if producer.getAction(action)==None:
                continue

            actionrunobj = producer.state.getSet(action)
            # print (actionrunobj)
            if actionrunobj.state != "OK":
                producersChanged.add(producer)

        if scope!=None:
            producersChanged=producersChanged.intersection(scope)

        return producersChanged


    def getNode(self):
        for parent in self.parents:
            if 'ssh' == parent.role:
                return parent
        return None

    def isOnNode(self,node=None):
        mynode = self.getNode()
        if mynode is None:
            return False
        return mynode.key == node.key


    def getTCPPorts(self, processes=None, *args, **kwargs):
        ports = set()
        if processes is None:
            processes = self.getProcessDicts()
        for process in self.getProcessDicts():
            for item in process.get("ports", []):
                if isinstance(item, str):
                    moreports = item.split(";")
                elif isinstance(item, int):
                    moreports = [item]
                for port in moreports:
                    if isinstance(port, int) or port.isdigit():
                        ports.add(int(port))
        return list(ports)

    def getPriority(self):
        processes = self.getProcessDicts()
        if processes:
            return processes[0].get('prio', 100)
        return 199

    def getProcessDicts(self, args={}):
        return getProcessDicts(self, args={})

    # def getDependencyChain(self, chain=None):
    #     chain = chain if chain is not None else []
    #     dependencies = self.getDependencies()
    #     for dep in dependencies:
    #         dep.getDependencyChain(chain)
    #         if self in chain:
    #             if dep not in chain:
    #                 chain.insert(chain.index(self)+1, dep)
    #             if dep in chain and chain.index(dep) > chain.index(self):
    #                 dependant = chain.pop(self)
    #                 chain.insert(chain.index(dep), dependant)
    #         else:
    #             if dep not in chain:
    #                 chain.append(dep)
    #     return chain


    def _downloadFromNode(self):
        # if 'os' not in self.producers or self.executor is None:
        if not self.parent or self.parent.role != 'ssh':
            return

        hrd_root = "/etc/ays/local/"
        remotePath = j.sal.fs.joinPaths(hrd_root, j.sal.fs.getBaseName(self.path), 'instance.hrd')
        dest = self.path.rstrip("/")+"/"+"instance.hrd"
        self.logger.info("downloading %s '%s'->'%s'" % (self.key, remotePath, self.path))
        self.executor.download(remotePath, self.path)

    def _getExecutor(self):
        executor = None
        tocheck = [self]
        tocheck.extend(self.parents)
        for service in tocheck:
            if hasattr(service.actions, 'getExecutor'):
                executor = service.actions.getExecutor()
                return executor
        return j.tools.executor.getLocal()

    def log(self, msg, level=0):
        self.action_current.log(msg)

    def listChildren(self):


        childDirs = j.sal.fs.listDirsInDir(self.path)
        childs = {}
        for path in childDirs:
            if path.endswith('__pycache__'):
                continue
            child = j.sal.fs.getBaseName(path)
            name, instance = child.split("!")
            if name not in childs:
                childs[name] = []
            childs[name].append(instance)
        return childs

    @property
    def children(self):
        res=[]
        for key,service in j.atyourservice.services.items():
            if service.parent==self:
                res.append(service)
        return res

    def isConsumedBy(self, service):
        if self.role in service.producers:
            for s in service.producers[self.role]:
                if s.key == self.key:
                    return True
        return False

    # def _consume(self, producerservice, producercategory):
    #     """
    #     create connection between consumer (this service) & producer
    #     producer category is category of service
    #     @param producerservice is service or servicekey
    #     """
    #     if j.data.types.string.check(producerservice):
    #         producerservice = j.atyourservice.getServiceFromKey(producerservice)
    #     key = "producer.%s" % producercategory
    #     val = self.hrd.get(key, "").strip().strip("'").strip()
    #     if val.find(producerservice.key) == -1:
    #         if val != "":
    #             val = "%s,%s" % (val, producerservice.key)
    #         else:
    #             val = "%s" % producerservice.key
    #         self.hrd.set(key, val)

    #         self.init()

    def getProducers(self, producercategory):
        if producercategory not in self.producers:
            raise j.exceptions.Input("cannot find producer with category:%s" % producercategory)
        instances = self.producers[producercategory]
        return instances

    def __eq__(self, service):
        if not service:
            return False
        if isinstance(service, str):
            return j.atyourservice.getKey(self) == service
        return service.role == self.role and self.instance == service.instance

    def __hash__(self):
      return hash((self.domain, self.name, self.instance, self.role, self.version))

    def __repr__(self):
        # return '%s|%s!%s(%s)' % (self.domain, self.name, self.instance, self.version)
        return self.key

    def __str__(self):
        return self.__repr__()

    # # ACTIONS
    # # def _executeOnNode(self, actionName, cmd=None, reinstall=False):
    # def _executeOnNode(self, actionName):
    #     if not self.parent or self.parent.role != 'ssh':
    #     # if 'os' not in self.producers or self.executor is None:
    #         return False
    #     self._uploadToNode()

    #     execCmd = 'source /opt/jumpscale8/env.sh; aysexec do %s %s %s' % (actionName, self.role, self.instance)

    #     executor = self.executor
    #     executor.execute(execCmd, die=True, showout=True)

    #     return True

    def runAction(self, action, printonly=False,ignorestate=False, force=False):

        self.actions.service=self
        a=self.getAction(action)

        if force:
            self.state.set(methodname=action, state="DO")

        #when none means does not exist so does not have to be executed
        if a!=None:
            if printonly==False:
                return a()
            else:
                print ("Execute: %s %s"%(self,action))

        #@todo implement ignorestate (not so easy)

    def getAction(self,action):
        """
        @return None when not exist
        """
        try:
            a=getattr(self.actions, action)
        except Exception as e:
            if str(e).find("object has no attribute")!=-1:
                return None
            raise Exception(e)
        return a

    def _getDisabledProducers(self):
        producers = dict()
        for key, items in self.hrd.getDictFromPrefix("producer").items():
            producers[key] = [j.atyourservice.getServiceFromKey(item.strip(), include_disabled=True) for item in items]
        return producers

    def _getConsumers(self, include_disabled=False):
        consumers = list()
        services = j.atyourservice.findServices(include_disabled=True, first=False)
        for service in services:
            producers = service._getDisabledProducers() if include_disabled else service.producers
            if self.role in producers and self in producers[self.role]:
                consumers.append(service)
        return consumers

    def disable(self):
        self.stop()
        for consumer in self._getConsumers():
            candidates = j.atyourservice.findServices(role=self.role, first=False)
            if len(candidates) > 1:
                # Other candidates available. Should link consumer to new candidate
                candidates.remove(self)
                candidate = candidates[0]
                producers = consumer.hrd.getList('producer.%s' % self.role, [])
                producers.remove(self.key)
                producers.append(candidate.key)
                consumer.hrd.set('producer.%s' % self.role, producers)
            else:
                # No other candidates already installed. Disable consumer as well.
                consumer.disable()

        self.log("disable instance")
        self.state.hrd.set('disabled', True)

    def _canBeEnabled(self):
        for role, producers in list(self.producers.items()):
            for producer in producers:
                if producer.state.hrd.getBool('disabled', False):
                    return False
        return True

    def enable(self):
        # Check that all dependencies are enabled

        if not self._canBeEnabled():
            self.log("%s cannot be enabled because one or more of its producers is disabled" % self)
            return

        self.state.hrd.set('disabled', False)
        self.log("Enable instance")
        for consumer in self._getConsumers(include_disabled=True):
            consumer.enable()
            consumer.start()
