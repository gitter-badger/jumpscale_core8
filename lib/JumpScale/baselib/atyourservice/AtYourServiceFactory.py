from JumpScale import j
from ServiceTemplate import ServiceTemplate
from ServiceRecipe import ServiceRecipe
from Service import Service, loadmodule
from ActionsBaseNode import ActionsBaseNode
from ActionMethodDecorator import ActionMethodDecorator
from Blueprint import Blueprint
# from AYSdb import *

from AtYourServiceSync import AtYourServiceSync
try:
    from AtYourServiceSandboxer import *
except:
    pass
import os


import colored_traceback
colored_traceback.add_hook(always=True)

class AtYourServiceFactory():

    def __init__(self):
        self.__jslocation__ = "j.atyourservice"

        self._init = False
        self._domains = []
        self.hrd = None
        self._justinstalled = []
        self._type = None
        self._services = {}
        self._templates = []
        self._recipes = []
        self.indocker = False
        self.sync = AtYourServiceSync()
        self._reposDone = {}
        self._todo = []
        self.debug=j.core.db.get("atyourservice.debug")==1
        self._basepath=None
        self._git=None
        self._blueprints=[]
        self._sandboxer=None
        self._roletemplates = dict()
        self._servicesTree = {}
        # self._db=AYSDB()

    def reset(self):
        # self._db.reload()
        j.dirs._ays = None
        self._services = {}
        self._templates = []
        self._recipes = []
        self._reposDone = {}
        self._todo = []
        self._git=None
        self._blueprints=[]
        self._servicesTree = {}

    def destroy(self,uninstall=True):
        if uninstall:
            self.uninstall()
        j.sal.fs.removeDirTree(j.sal.fs.joinPaths(self.basepath,"recipes"))
        j.sal.fs.removeDirTree(j.sal.fs.joinPaths(self.basepath,"services"))

    @property
    def basepath(self):
        if self._basepath==None:
            self.basepath=j.sal.fs.getcwd()
        return self._basepath

    @basepath.setter
    def basepath(self,val):
        self.reset()
        baseDir=val
        while j.sal.fs.joinPaths(baseDir, ".ays") not in j.sal.fs.listFilesInDir(baseDir, recursive=False):
            baseDir=j.sal.fs.getParent(baseDir)
            baseDir=baseDir.rstrip("/")

            if baseDir.strip()=="":
                if 'darwin' in j.core.platformtype.myplatform.platformtypes:
                    baseDir = "%s/ays/"%j.dirs.cfgDir
                else:
                    baseDir = "/etc/ays/local"
                break

        self._basepath=baseDir
        for item in ["blueprints","recipes","services","servicetemplates"]:
            #make sure basic dirs exist
            j.sal.fs.createDir(j.sal.fs.joinPaths(self._basepath,item))

    @property
    def git(self):
        if self._git==None:
            self._git=j.clients.git.get(basedir=self.basepath)
        return self._git

    @property
    def sandboxer(self):
        if self._sandboxer==None:
            self._sandboxer=AtYourServiceSandboxer()
        return self._sandboxer

    @property
    def type(self):
        if self._type is not None:
            return self._type
        self._type = "n"  # n from normal
        # check if we are in a git directory, if so we will use $thatdir/services as base for the metadata
        if self.basepath is not None:
            self._type = "c"
        return self._type

    @property
    def domains(self):
        self._doinit()
        return self._domains

    @property
    def templates(self):
        self._doinit()
        def load(domain, path, llist):
            for servicepath in j.sal.fs.listDirsInDir(path, recursive=False):
                dirname = j.sal.fs.getBaseName(servicepath)
                # print "dirname:%s"%dirname
                if not (dirname.startswith(".")):
                    load(domain, servicepath, llist)
            # print path
            dirname = j.sal.fs.getBaseName(path)
            if dirname.startswith("_"):
                return
            tocheck = ['schema.hrd', 'service.hrd', 'actions_mgmt.py', 'actions_node.py', 'model.py', 'actions.py']
            exists = [True for aysfile in tocheck if j.sal.fs.exists('%s/%s' % (path, aysfile))]
            if exists:
                templ = ServiceTemplate(path, domain=domain)
                llist.append(templ)

        if not self._templates:
            self._doinit()

            # load local templates
            path = j.sal.fs.joinPaths(self.basepath, "servicetemplates/")
            load("ays", path, self._templates)

            for domain, domainpath in self.domains:
                # print "load template domain:%s"%domainpath
                load(domain, domainpath, self._templates)

        return self._templates

    @property
    def recipes(self):
        self._doinit()
        if not self._recipes:
            self._doinit()
            aysrepopath = self.basepath
            if aysrepopath is not None:
                # load local templates
                domainpath = j.sal.fs.joinPaths(aysrepopath, "%s/recipes/" % aysrepopath)
                d = j.tools.path.get(domainpath)
                for item in d.walkfiles("state.hrd"):
                    recipepath = j.sal.fs.getDirName(item)
                    self._recipes.append(ServiceRecipe(recipepath))
        return self._recipes

    @property
    def services(self):
        self._doinit()
        if self._services == {}:
            for hrd_path in j.sal.fs.listFilesInDir(j.dirs.ays, recursive=True, filter="instance.hrd",
                                                    case_sensitivity='os', followSymlinks=True, listSymlinks=False):
                service_path = j.sal.fs.getDirName(hrd_path)
                service = Service(path=service_path, args=None)
                self._services[service.key]=service
        return self._services

    def _nodechildren(self, service, parent=None, producers=[]):
        parent = {} if parent is None else parent
        me = {"name": service.key, "children": []}
        parent["children"].append(me)
        details = service.hrd.getHRDAsDict()
        details = {key: value for key, value in details.items() if key not in ['service.domain', 'service.name', 'service.version', 'parent']}
        me["data"] = details
        children = service.listChildren()
        for role, instances in children.items():
            for instance in instances:
                child = j.atyourservice.getService(role=role, instance=instance)
                for _, producerinstances in child.producers.items():
                    for producer in producerinstances:
                        producers.append([child.key, producer.key])
                self._nodechildren(child, me, producers)
        return parent

    @property
    def servicesTree(self):
        if self._servicesTree:
            return self._servicesTree
        self._doinit()
        producers = []
        parents = {"name": "sudoroot", "children": []}
        for root in j.sal.fs.walk(j.dirs.ays, recurse=1, pattern='*instance.hrd', return_files=1, depth=2):
            servicekey = j.sal.fs.getBaseName(j.sal.fs.getDirName(root))
            service = self.services.get(servicekey)
            for _, producerinstances in service.producers.items():
                for producer in producerinstances:
                    producers.append([child.key, producer.key])
            parents["children"].append(self._nodechildren(service, {"children": [], "name": servicekey}, producers))
        self._servicesTree['parentchild'] = parents
        self._servicesTree['producerconsumer'] = producers
        return self._servicesTree

    @property
    def blueprints(self):
        """
        """
        if self._blueprints==[]:
            items=j.sal.fs.listFilesInDir(self.basepath+"/blueprints")
            items=[item for item in items if item.find("_archive")==-1]
            items=[item for item in items if item[0]!="_"]
            items.sort()
            for path in items:
                self._blueprints.append(Blueprint(path))
        return self._blueprints

    @property
    def roletemplates(self):
        if self._roletemplates:
            return self._roletemplates
        templatespaths = [j.sal.fs.joinPaths(self.basepath, '_templates')]
        for _, metapath in self._domains:
            templatespaths.append(j.sal.fs.joinPaths(metapath, '_templates'))
        templatespaths.reverse()

        for templatespath in templatespaths:
            if j.sal.fs.exists(templatespath):
                for roletemplate in j.sal.fs.listDirsInDir(templatespath):
                    paths = ['schema_tmpl.hrd', 'actions_tmpl_mgmt.py', 'actions_tmpl_node.py']
                    rtpaths = [path for path in paths if j.sal.fs.exists(j.sal.fs.joinPaths(templatespath, roletemplate, path))]
                    if rtpaths:
                        self._roletemplates[j.sal.fs.getBaseName(roletemplate)] = [j.sal.fs.joinPaths(roletemplate, rtpath) for rtpath in rtpaths]
        return self._roletemplates

    def _doinit(self):
        # if we don't have write permissin on /opt don't try do download service templates
        opt = j.tools.path.get('/opt')
        if not opt.access(os.W_OK):
            self._init = True

        if self._init is False:

            j.actions.setRunId("ays_%s"%j.sal.fs.getBaseName(j.atyourservice.basepath))
            # j.actions.reset()

            # self.logger = j.logger.get()

            # j.do.debug=True

            if j.sal.fs.exists(path="/etc/my_init.d"):
                self.indocker=True

            login=j.application.config.get("whoami.git.login").strip()
            passwd=j.application.config.getStr("whoami.git.passwd").strip()

            # always load base domaim
            items=j.application.config.getDictFromPrefix("atyourservice.metadata")
            repos=j.do.getGitReposListLocal()

            for domain in list(items.keys()):
                url=items[domain]['url']
                if url.strip()=="":
                    raise j.exceptions.RuntimeError("url cannot be empty")
                branch=items[domain].get('branch', 'master')
                reponame=url.rpartition("/")[-1]
                if not reponame in list(repos.keys()):
                    # means git has not been pulled yet
                    if login!="":
                        dest=j.do.pullGitRepo(url,dest=None,login=login,passwd=passwd,depth=1,ignorelocalchanges=False,reset=False,branch=branch)
                    else:
                        dest=j.do.pullGitRepo(url,dest=None,depth=1,ignorelocalchanges=False,reset=False,branch=branch)

                repos=j.do.getGitReposListLocal()

                dest=repos[reponame]
                # print "init %s" % domain
                self._domains.append((domain,dest))

        self._init=True

    def init(self,role="",instance="",newrun=True):

        self.reset()

        # make sure the recipe's are loaded & initted
        for bp in self.blueprints:
            bp.loadrecipes()

        # start from clean sheet
        self.reset()

        for bp in self.blueprints:
            bp.execute(role=role,instance=instance)

        print ("init done")

    def createAYSRepo(self, path):
        j.sal.fs.createDir(path)
        j.sal.fs.createEmptyFile(j.sal.fs.joinPaths(path, '.ays'))
        j.sal.fs.createDir(j.sal.fs.joinPaths(path, 'servicetemplates'))
        j.sal.fs.createDir(j.sal.fs.joinPaths(path, 'blueprints'))
        j.sal.process.execute("git init %s" % path, die=True, outputToStdout=False, useShell=False, ignoreErrorOutput=False)
        j.sal.nettools.download('https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore', j.sal.fs.joinPaths(path, '.gitignore'))
        print("AYS Repo created at %s" % path)

    def updateTemplatesRepos(self, repos=[]):
        """
        update the git repo that contains the service templates
        args:
            repos : list of dict of repos to update, if empty, all repos are updated
                    {
                        'url' : 'http://github.com/account/repo',
                        'branch' : 'master'
                    }
        """
        if len(repos) == 0:
            metadata = j.application.config.getDictFromPrefix('atyourservice.metadata')
            repos = list(metadata.values())

        for repo in repos:
            branch = repo['branch'] if 'branch' in repo else 'master'
            j.do.pullGitRepo(url=repo['url'], branch=branch)

    def getActionsBaseClassNode(self):
        return ActionsBaseNode


    def getActionMethodDecorator(self):
        return ActionMethodDecorator

    def getBlueprint(self,path):
        if not j.sal.fs.exists(path):
            path=self.basepath+"/"+path
        return Blueprint(path)

    def getRoleTemplateClass(self, role, ttype):
        if role not in self.roletemplates:
            raise j.exceptions.RuntimeError('Role template %s does not exist' % role)
        roletemplatepaths = self.roletemplates[role]
        for roletemplatepath in roletemplatepaths:
            if ttype in j.sal.fs.getBaseName(roletemplatepath):
                modulename = "JumpScale.atyourservice.roletemplate.%s.%s" % (role, ttype)
                mod = loadmodule(modulename, roletemplatepath)
                return mod.Actions
        return None

    def getRoleTemplateHRD(self, role):
        if role not in self.roletemplates:
            raise j.exceptions.RuntimeError('Role template %s does not exist' % role)
        roletemplatepaths = self.roletemplates[role]
        hrdpaths = [path for path in roletemplatepaths if j.sal.fs.getFileExtension(path) == 'hrd']
        if hrdpaths:
            hrd = j.data.hrd.getSchema(hrdpaths[0])
            for path in hrdpaths[1:]:
                hrdtemp = j.data.hrd.getSchema(path)
                hrd.items.update(hrdtemp.items)
            return hrd.hrdGet()
        return None
    def uninstall(self, printonly=False, remember=True):
        self.do(action="uninstall", printonly=printonly)


    def install(self,role="", instance="",printonly=False,ignorestate=False):
        self.do(action="install",role=role,instance=instance,printonly=printonly,ignorestate=ignorestate)

    def apply(self, role="", instance="",printonly=False, remember=True):
        self.do("start",role,instance)  #will make sure init & install happened first

    def commit(self, action="unknown", msg="", precheck=False):
        pass
        # if len(self.git.getModifiedFiles(True,ignore=["/alog/"]))>0:
        #     if msg=="":
        #         msg='ays changed, commit changed files for action:%s'%action
        #     print(msg)
        #     repo=self.git.commit(message=msg, addremove=True)
        #     self.alog.newGitCommit(action=action,githash=repo.hexsha)
        # else:
        #     #@todo will create duplicates will have to fix that
        #     #git hash is current state
        #     if not precheck:
        #         #only do this when no precheck, means we are not cleaning up past
        #         self.alog.newGitCommit(action=action,githash="")

    # def _getChangedServices(self, action=None):
    #     changed = list()
    #     if not action:
    #         actions = ["install", "stop", "start", "monitor", "halt", "check_up", "check_down",
    #                    "check_requirements", "cleanup", "data_export", "data_import", "uninstall", "removedata"]
    #     else:
    #         actions = [action]
    #     for _, service in self.services.items():
    #         if [service for action in actions if service.state.getSet(action).state == 'CHANGED']:
    #             changed.append(service)
    #             for producers in [producers for _, producers in service.producers.items()]:
    #                 changed.extend(producers)
    #     return changed


    def do(self, action="install", role="", instance="", printonly=False, ignorestate=False, force=False, ask=False):

        #make sure actions which are relevant get their init & install done
        if action != "init" and action != "uninstall":
            self.do("init",role=role,instance=instance)

        if action != "init" and action != "install" and action != "uninstall":
            self.do("install",role=role,instance=instance)

        todo = self.findTodo(action=action,role=role,instance=instance,force=force,ignorestate=ignorestate or printonly)

        step = 1
        while todo != []:

            if ask:
                from IPython import embed
                print ("DEBUG NOW ask in do, filter items")
                embed()
                

            print("execute state changes, nr services to process: %s in step:%s" % (len(todo), step))
            for i in range(len(todo)):
                service = todo[i]
                print ("DO:%s %s"%(service,action))
                service.runAction(action, printonly=printonly,ignorestate= ignorestate, force=force)

            todo = self.findTodo(action=action)

    def findTodo(self, action="install",role="",instance="",force=False,ignorestate=False):


        #change the state so for sure these will be executed
        if force:
            todo = [item[1] for item in self.services.items()]
            for service in todo:

                #skip the ones which are not part of the filter for role & instance
                if role!="" and service.role!=role:
                    continue
                if instance!="" and service.instance!=instance:
                    continue

                state = service.state.getSet(action)
                if ignorestate:
                    state._state = "DO" #this should make sure its not being set in state file
                else:
                    state.state = "DO"

        #create a scope in which we need to find work
        scope=set()
        for key, service in self.services.items():
            if role!="" and service.role!=role:
                continue
            if instance!="" and service.instance!=instance:
                continue
            scope.add(service)
            producersl=service.getProducersRecursive()
            scope=scope.union(producersl)

        #now we need to go over all but limited to scope
        todo = list()
        for service in scope:
            actionstate = service.state.getSet(action)
            if actionstate.state != "OK":
                producersWaiting = service.getProducersWaiting(action, set(),scope=scope)
                # print ("%s:\n%s"%(action,producersWaiting))                
                if len(producersWaiting) == 0:
                    if service.getAction(action)!=None:
                        todo.append(service)
                        if j.atyourservice.debug:
                            print("%s waiting for %s" % (service,action))
                    else:
                        if j.atyourservice.debug:
                            print("%s no need to do '%s' because method does not exist." % (service,action))

                elif j.application.debug:
                    print("%s no producers waiting for action %s" % (service,action))
        return todo


    def findTemplates(self, name="", version="", domain="", role='', first=False):
        res = []
        for template in self.templates:
            if not(name == "" or template.name == name):
                # no match continue
                continue
            if not(domain == "" or template.domain == domain):
                # no match continue
                continue
            if not(version == "" or template.version == version):
                # no match continue
                continue
            if not (role == '' or template.role == role):
                # no match continue
                continue
            res.append(template)

        if first:
            if len(res) == 0:
                raise j.exceptions.Input("cannot find service template %s:%s (%s)" % (domain, name, version), "ays.findTemplates")
            return res[0]
        return res

    def findRecipes(self, name="", version="", role='',one=False):
        res = []
        domain="ays"
        for template in self.recipes:
            if not(name == "" or template.name == name):
                # no match continue
                continue
            if not(domain == "" or template.domain == domain):
                # no match continue
                continue
            if not(version == "" or template.version == version):
                # no match continue
                continue
            if not (role == '' or template.role == role):
                # no match continue
                continue
            res.append(template)

        if one:
            if len(res) == 0:
                raise j.exceptions.Input("cannot find ays recipes %s|%s (%s)" % (domain, name, version), "ays.findRecipes")
            if len(res) > 1:
                raise j.exceptions.Input("found 2+ ays recipes %s|%s (%s)" % (domain, name, version), "ays.findRecipes")
            return res[0]

        return res

    def findAYSRepos(self):
        return (root for root, dirs, files in os.walk(j.dirs.codeDir) if '.ays' in files)

    def findServices(self, name="", instance="",version="", domain="", parent=None, first=False, role="", node=None, include_disabled=False):
        res = []

        for key, service in self.services.items():
            # if service._state and service._state.hrd.getBool('disabled', False) and not include_disabled:
            #     continue
            if not(name == "" or service.name == name):
                continue
            if not(domain == "" or service.domain == domain):
                continue
            if not(version == "" or service.version == version):
                continue
            if not(instance == "" or service.instance == instance):
                continue
            if not(parent is None or service.parent == parent):
                continue
            if not(role == "" or role == service.role):
                continue
            if not(node is None or service.isOnNode(node)):
                continue
            res.append(service)
        if first:
            if len(res) == 0:
                raise j.exceptions.Input("cannot find service %s|%s:%s (%s)" % (domain, name, instance, version), "ays.findServices")
            return res[0]
        return res

    def findProducer(self, producercategory, instancename):
        for item in self.findServices(instance=instancename):
            if producercategory in item.categories:
                return item

    def findConsumers(self, target):
        """
        @return set of services that consumes target
        """
        result = set()
        for service in self.findServices():
            if target.isConsumedBy(service):
                result.add(service)
        return result

    def findConsumersRecursive(self, target, out=set()):
        """
        @return set of services that consumes target, recursivlely
        """
        for service in self.findConsumers(target):
            out.add(service)
            self.findConsumersRecursive(service, out)
        return out

    def new(self,  name="", instance="main",version="",domain="",path=None, parent=None, args={},consume=""):
        """
        will create a new service from template

        @param args are the arguments which will overrule questions of the instance.hrd
        @param consume specifies which ays instances will be consumed
                format $role/$domain|$name!$instance,$role2/$domain2|$name2!$instance2

        """
        recipe = self.getRecipe(name,domain,version)
        obj = recipe.newInstance(instance=instance, path=path, parent=parent, args=args, consume=consume)
        return obj

    def remove(self,  name="", instance="",domain="", role=""):
        for service in self.findServices(domain=domain, name=name, instance=instance, role=role):
            if service in self.services:
                self.services.remove(service)
            j.sal.fs.removeDirTree(service.path)

    def getTemplate(self,  name="", version="",domain="", role="", first=True, die=True):
        if first:
            return self.findTemplates(domain=domain, name=name, version=version, role=role, first=first)
        else:
            res = self.findTemplates(domain=domain, name=name, version=version, role=role, first=first)
            if len(res) > 1:
                if die:
                    raise j.exceptions.Input("Cannot get ays template '%s|%s (%s)', found more than 1" % (domain, name, version), "ays.gettemplate")
                else:
                    return
            if len(res) == 0:
                if die:
                    raise j.exceptions.Input("Cannot get ays template '%s|%s (%s)', did not find" % (domain, name, version), "ays.gettemplate")
                else:
                    return
            return res[0]

    def getRecipe(self, name="",version="", domain="", role=""):
        template = self.getTemplate(domain=domain,name=name, version=version, role=role)
        return template.recipe

    def getService(self, role='', instance='main', die=True):
        """
        Return service indentifier by domain,name and instance
        throw error if service is not found or if more than one service is found
        """
        key="%s!%s"%(role,instance)
        if key in self.services:
            return self.services[key]
        if die:
            raise j.exceptions.Input("Cannot get ays service '%s', did not find" % key, "ays.getservice")
        else:
            return None

        return res[0]

    def getKey(self, service):
        """

        different formats

        for services:
        ```$role!$instance```

        for servicetemplates or servicerecipes
        ```$domain|$name``` if domain is not empty or not ays

        """
        if isinstance(service,Service):
            key = service.role
            key += "!%s" % (service.instance)
        elif isinstance(service,ServiceTemplate) or isinstance(service,ServiceRecipe):

            if service.domain != "" and service.domain != "ays" :
                key = "%s|%s" % (service.domain, service.name)
            else:
                key = service.name
        # if service.version != "":
        #     key += " (%s)" % service.version
        return key.lower()

    def getServiceFromKey(self, key):
        """
        key in format $domain|$name!$instance@role ($version)

        different formats
        - @$role!$instance or $role!$instance
        - !$instance
        - @role

        examples
        - find me service with role ns: '@ns' if more than 1 then there will be an error
        - find me a service with instance name ovh4 '!ovh4'

        """
        domain, name, version, instance, role = self.parseKey(key)
        return self.getService(instance=instance,role=role, die=True)

    def parseKey(self, key):
        """
        @return (domain,name,version,instance,role)

        """
        key = key.lower()
        if key.find("|") != -1:
            domain, name = key.split("|")
        else:
            domain = ""
            name = key

        if name.find("@") != -1:
            name, role = name.split("@", 1)
            role = role.strip()
        else:
            role = ""

        if name.find("!") != -1:
            # found instance
            name, instance = name.split("!", 1)
            if instance.find("(") != -1:
                instance, version = instance.split("(", 1)
                name += "(%s" % version
            instance = instance.strip()
            if domain == '':
                role = name
                name = ''
        else:
            instance = ""

        if name.find("(") != -1:
            name, version = name.split("(", 1)
            version = version.split(")", 1)[0]
        else:
            version = ""
        name = name.strip()

        if role == "":
            if name.find('.') != -1:
                role = name.split(".", 1)[0]
            else:
                role = name

        domain = domain.strip()
        version = version.strip()
        return (domain, name, version, instance, role)

    def __str__(self):
        return self.__repr__()

    def telegramBot(self, token, start=True):
        from JumpScale.baselib.atyourservice.telegrambot.TelegramAYS import TelegramAYS
        bot = TelegramAYS(token)
        if start:
            bot.run()
        return bot
