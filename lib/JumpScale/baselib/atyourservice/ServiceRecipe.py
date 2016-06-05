from JumpScale import j

# import JumpScale.baselib.actions
import copy
import inspect

from ServiceTemplate import ServiceTemplate


from Service import Service, loadmodule

DECORATORCODE = """
ActionMethodDecorator=j.atyourservice.getActionMethodDecorator()
ActionsBaseMgmt=j.atyourservice.getActionsBaseClassMgmt()

class action(ActionMethodDecorator):
    def __init__(self,*args,**kwargs):
        ActionMethodDecorator.__init__(self,*args,**kwargs)

"""

class RecipeState():

    def __init__(self, recipe):
        self.recipe=recipe

        self._path = j.sal.fs.joinPaths(self.recipe.path, "state.json")
        if j.sal.fs.exists(path=self._path):
            self._model=j.data.serializer.json.load(self._path)
        else:
            self._model={"methods":{}}

        self.changed=False
        self._changes={}
        self._methodsList=[]

    def addMethod(self,name="",source="",isDefaultMethod=False):
        if source!="":
            if name in ["input","init"]:
                if source.find("$(")!=-1:
                    raise j.exceptions.Input("Action method:%s should not have template variable '$(...' in sourcecode for init or input method."%(self))

            if not isDefaultMethod:
                newhash=j.data.hash.md5_string(source)
                if name not in self._model["methods"] or newhash!=self._model["methods"][name]:
                    self._changes[name]=True
                    self._model["methods"][name]=newhash
                    self.changed=True
            else:
                self._model["methods"][name]=""

    def methodChanged(self,name):
        if name in self._changes:
            return True
        return False

    @property
    def methods(self):
        return self._model["methods"]

    @property
    def methodslist(self):
        """
        sorted methods
        """
        if self._methodsList==[]:
            keys=[item for item in self.methods.keys()]
            keys.sort()
            for key in keys:
                self._methodsList.append(self.methods[key])
        return self._methodsList

    def save(self):
        if self.changed:
            self.recipe.logger.info ("Recipe state Changed, writen to disk.")
            out=j.data.serializer.json.dumps(self._model,True,True)
            j.sal.fs.writeFile(filename=self._path,contents=out)
            self.changed=False

    def __repr__(self):
        out=""
        for item in self.methodslist:
            out+="%s\n"%item
        return out

    __str__ = __repr__




class ServiceRecipe(ServiceTemplate):

    def __init__(self, aysrepo,path="", template=None):

        self.aysrepo=aysrepo

        self.logger=self.aysrepo.logger


        if path != "":
            if not j.sal.fs.exists(path):
                raise j.exceptions.RuntimeError("Could not find path for recipe")
            self.name = j.sal.fs.getBaseName(path)
            self._path=path
        else:
            if template==None:
                raise RuntimeError("template cannot be None")
            self.name=template.name
            self._path=None

        self._init_props()

        self.state=RecipeState(self)

        self.role=self.name.split(".",1)[0]


        # copy the files
        if not j.sal.fs.exists(path=self.path):
            j.sal.fs.createDir(self.path)
            self.init()

    def _init_props(self):
        self._hrd = None
        self._schema = None
        self._actions = None
        self._name=None
        self._domain=None
        self._recipe=None
        self._template=None
        self.path_hrd_template = j.sal.fs.joinPaths(self.path, "service.hrd")
        self.path_hrd_schema = j.sal.fs.joinPaths(self.path, "schema.hrd")
        self.path_actions = j.sal.fs.joinPaths(self.path, "actions.py")
        self.path_actions_node = j.sal.fs.joinPaths(self.path, "actions_node.py")
        # self.path_mongo_model = j.sal.fs.joinPaths(self.path, "model.py")

    @property
    def path(self):
        if self._path==None:
            self._path = j.sal.fs.joinPaths(self.aysrepo.basepath, "recipes", self.template.name)
        return self._path

    @property
    def template(self):
        if self._template==None:
            self._template = self.aysrepo.getTemplate(self.name)
        return self._template

    @property
    def domain(self):
        if self._domain==None:
            self._domain = self.template.domain
        return self._domain

    @property
    def recipe(self):
        if self._recipe==None:
            self._recipe = self.aysrepo.getRecipe(self.name)
        return self._recipe


    def init(self):

        self.state._changes={}

        if j.sal.fs.exists(self.template.path_hrd_template):
            j.sal.fs.copyFile(self.template.path_hrd_template, self.path_hrd_template)
        if j.sal.fs.exists(self.template.path_hrd_schema):
            j.sal.fs.copyFile(self.template.path_hrd_schema, self.path_hrd_schema)
        if j.sal.fs.exists(self.template.path_actions_node):
            j.sal.fs.copyFile(self.template.path_actions_node, self.path_actions_node)
        if j.sal.fs.exists(self.template.path_mongo_model):
            j.sal.fs.copyFile(self.template.path_mongo_model, self.path_mongo_model)

        self._writeActionsFile()

        self.state.save()

    def _writeActionsFile(self):
        self._out = ""

        actionmethodsRequired = ["input", "init", "install", "stop", "start", "monitor", "halt", "check_up", "check_down",
                                 "check_requirements", "cleanup", "data_export", "data_import", "uninstall", "removedata", "consume"]

        if j.sal.fs.exists(self.template.path_actions):
            content = j.sal.fs.fileGetContents(self.template.path_actions)
        else:
            content = "class Actions(ActionsBaseMgmt):\n\n"

        if content.find("class action(ActionMethodDecorator)") != -1:
            raise j.exceptions.Input("There should be no decorator specified in %s" % self.path_actions)

        content = "%s\n\n%s" % (DECORATORCODE, content)

        content = content.replace("from JumpScale import j", "")
        content = "from JumpScale import j\n\n%s" % content

        state = "INIT"
        amSource = ""
        amName = ""

        # DO NOT CHANGE TO USE PYTHON PARSING UTILS
        lines = content.splitlines()
        size = len(lines)
        i = 0

        while i < size:
            line = lines[i]
            linestrip = line.strip()
            if state == "INIT" and linestrip.startswith("class Actions"):
                state = "MAIN"
                i += 1
                continue

            if state == "MAIN" and linestrip.startswith("@"):
                if amSource!="":
                    self.state.addMethod(amName, amSource)
                amSource = ""
                amName = ""
                i += 1
                continue

            if state == "MAIN" and linestrip.startswith("def"):
                if amSource!="":
                    self.state.addMethod(amName,amSource)
                amSource=linestrip+"\n"
                amName=linestrip.split("(",1)[0][4:].strip()
                # make sure the required method have the action() decorator
                if amName in actionmethodsRequired and not lines[i-1].strip().startswith('@') and amName not in ["input"]:
                    lines.insert(i, '\n    @action()')
                    size += 1
                    i+=1

                i += 1
                continue

            if amName !="":
                amSource += "%s\n" % line[4:]
            i += 1


        #process the last one
        if amSource!="":
            self.state.addMethod(amName,amSource)

        content = '\n'.join(lines)

        # add missing methods
        for actionname in actionmethodsRequired:
            if actionname not in self.state.methods:
                am = self.state.addMethod(name=actionname,isDefaultMethod=True)
                #not found
                if actionname == "input":
                    content += '\n\n    def input(self, service, name, role, instance, serviceargs):\n        return serviceargs\n'
                else:
                    content += "\n\n    @action()\n    def %s(self, service):\n        return True\n" % actionname

        j.sal.fs.writeFile(self.path_actions, content)

        for key, _ in self.state.methods.items():
            if self.state.methodChanged(key):
                self.logger.info("method:%s    %s changed" % (key, self))
                for service in self.aysrepo.findServices(templatename=self.name):
                    service.actions.change_method(service, methodname=key)            
        self.state._changes = {}

    def get_actions(self, service):
        modulename = "JumpScale.atyourservice.%s.%s" % (self.name, service.instance)
        mod = loadmodule(modulename, self.path_actions)
        return mod.Actions()

    def newInstance(self, instance="main", args={}, path='', parent=None, consume="", originator=None, model=None):
        """
        """

        if parent is not None and instance == "main":
            instance = parent.instance

        instance = instance.lower()

        service = self.aysrepo.getService(role=self.role, instance=instance, die=False)

        if service is not None:
            # print("NEWINSTANCE: Service instance %s!%s  exists." % (self.name, instance))
            service._recipe = self
            service.init(args=args)
            if model is not None:
                service.model = model
        else:
            key = "%s!%s" % (self.role, instance)

            if path:
                fullpath = path
            elif parent is not None:
                fullpath = j.sal.fs.joinPaths(parent.path, key)
            else:
                ppath = j.sal.fs.joinPaths(self.aysrepo.basepath, "services")
                fullpath = j.sal.fs.joinPaths(ppath, key)

            if j.sal.fs.isDir(fullpath):
                j.events.opserror_critical(msg='Service with same role ("%s") and of same instance ("%s") is already installed.\nPlease remove dir:%s it could be this is broken install.' % (self.role, instance, fullpath))

            service = Service(aysrepo=self.aysrepo,servicerecipe=self, instance=instance, args=args, path="", parent=parent, originator=originator, model=model)

            self.aysrepo._services[service.key] = service

            # service.init(args=args)

        service.consume(consume)

        return service

    def downloadfiles(self):
        """
        this method download any required files for this recipe as defined in the template.hrd
        Use this method when building a service to have all the files ready to sandboxing

        @return list of tuples containing the source and destination of the files defined in the recipeitem
                [(src, dest)]
        """
        dirList = []
        # download
        for recipeitem in self.hrd_template.getListFromPrefix("web.export"):
            if "dest" not in recipeitem:
                j.events.opserror_critical(msg="could not find dest in hrditem for %s %s" % (recipeitem, self), category="ays.servicetemplate")

            fullurl = "%s/%s" % (recipeitem['url'],
                                 recipeitem['source'].lstrip('/'))
            dest = recipeitem['dest']
            dest = j.application.config.applyOnContent(dest)
            destdir = j.sal.fs.getDirName(dest)
            j.sal.fs.createDir(destdir)
            # validate md5sum
            if recipeitem.get('checkmd5', 'false').lower() == 'true' and j.sal.fs.exists(dest):
                remotemd5 = j.sal.nettools.download(
                    '%s.md5sum' % fullurl, '-').split()[0]
                localmd5 = j.data.hash.md5(dest)
                if remotemd5 != localmd5:
                    j.sal.fs.remove(dest)
                else:
                    continue
            elif j.sal.fs.exists(dest):
                j.sal.fs.remove(dest)
            j.sal.nettools.download(fullurl, dest)

        for recipeitem in self.hrd_template.getListFromPrefix("git.export"):
            if "platform" in recipeitem:
                if not j.core.platformtype.myplatform.checkMatch(recipeitem["platform"]):
                    continue

            # pull the required repo
            dest0 = self.aysrepo._getRepo(recipeitem['url'], recipeitem=recipeitem)
            src = "%s/%s" % (dest0, recipeitem['source'])
            src = src.replace("//", "/")
            if "dest" not in recipeitem:
                j.events.opserror_critical(msg="could not find dest in hrditem for %s %s" % (recipeitem, self), category="ays.servicetemplate")
            dest = recipeitem['dest']

            dest = j.application.config.applyOnContent(dest)
            src = j.application.config.applyOnContent(src)

            if "link" in recipeitem and str(recipeitem["link"]).lower() == 'true':
                # means we need to only list files & one by one link them
                link = True
            else:
                link = False

            if src[-1] == "*":
                src = src.replace("*", "")
                if "nodirs" in recipeitem and str(recipeitem["nodirs"]).lower() == 'true':
                    # means we need to only list files & one by one link them
                    nodirs = True
                else:
                    nodirs = False

                items = j.sal.fs.listFilesInDir(
                    path=src, recursive=False, followSymlinks=False, listSymlinks=False)
                if nodirs is False:
                    items += j.sal.fs.listDirsInDir(
                        path=src, recursive=False, dirNameOnly=False, findDirectorySymlinks=False)

                raise RuntimeError("getshort_key does not even exist")
                items = [(item, "%s/%s" % (dest, j.sal.fs.getshort_key(item)), link)
                         for item in items]
            else:
                items = [(src, dest, link)]

            out = []
            for src, dest, link in items:
                delete = recipeitem.get('overwrite', 'true').lower() == "true"
                if dest.strip() == "":
                    raise j.exceptions.RuntimeError(
                        "a dest in coderecipe cannot be empty for %s" % self)
                if dest[0] != "/":
                    dest = "/%s" % dest
                else:
                    if link:
                        if not j.sal.fs.exists(dest):
                            j.sal.fs.createDir(j.sal.fs.getParent(dest))
                            j.sal.fs.symlink(src, dest)
                        elif delete:
                            j.sal.fs.remove(dest)
                            j.sal.fs.symlink(src, dest)
                    else:
                        print(("copy: %s->%s" % (src, dest)))
                        if j.sal.fs.isDir(src):
                            j.sal.fs.createDir(j.sal.fs.getParent(dest))
                            j.sal.fs.copyDirTree(
                                src, dest, eraseDestination=False, overwriteFiles=delete)
                        else:
                            j.sal.fs.copyFile(
                                src, dest, True, overwriteFile=delete)
                out.append((src, dest))
                dirList.extend(out)

        return dirList

    def listInstances(self):
        """
        return a list of instance name for this template
        """
        services = self.aysrepo.findServices(templatename=self.name)
        return [service.instance for service in services]

    def upload2AYSfs(self, path):
        """
        tell the ays filesystem about this directory which will be uploaded to ays filesystem
        """
        j.tools.sandboxer.dedupe(path, storpath="/tmp/aysfs", name="md", reset=False, append=True)

    def __repr__(self):
        return "Recipe: %-15s" % (self.name)
