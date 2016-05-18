from JumpScale import j

from ServiceRecipe import ServiceRecipe
from Service import Service, loadmodule
from ServiceTemplate import ServiceTemplate

from ActionsBaseNode import ActionsBaseNode
from ActionsBaseMgmt import ActionsBaseMgmt
from ActionMethodDecorator import ActionMethodDecorator

from AtYourServiceRepo import AtYourServiceRepo

from AtYourServiceTester import AtYourServiceTester

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
        self._templates = {}

        # self.hrd = None

        self._type = None

        self.indocker = False

        # self.sync = AtYourServiceSync()
        # self._reposDone = {}

        self.debug=j.core.db.get("atyourservice.debug")==1

        self.logger=j.logger.get('j.atyourservice')

        self._repos={}

        self._test=None

    def getTester(self,name="main"):
        return AtYourServiceTester(name)

    def get(self,name,path=""):
        self._doinit()
        if path=="":
            path=j.sal.fs.getcwd()
        if not name in self._repos:
            self._repos[name]=AtYourServiceRepo(name,path)
        return self._repos[name]


    def reset(self):
        self._repos
        j.dirs._ays = None

    @property
    def repos(self):
        for path in j.atyourservice.findAYSRepos():
            name = j.sal.fs.getBaseName(path)
            self._repos[name] = AtYourServiceRepo(name, path)
        return self._repos

    @property
    def sandboxer(self):
        if self._sandboxer==None:
            self._sandboxer=AtYourServiceSandboxer()
        return self._sandboxer

    @property
    def domains(self):
        self._doinit()
        return self._domains

    @property
    def templates(self):
        self._doinit()
        def load(domain, path):
            for servicepath in j.sal.fs.listDirsInDir(path, recursive=False):
                dirname = j.sal.fs.getBaseName(servicepath)
                # print "dirname:%s"%dirname
                if not (dirname.startswith(".")):
                    load(domain, servicepath)
            # print path
            dirname = j.sal.fs.getBaseName(path)
            if dirname.startswith("_"):
                return
            tocheck = ['schema.hrd', 'service.hrd', 'actions_mgmt.py', 'actions_node.py', 'model.py', 'actions.py']
            exists = [True for aysfile in tocheck if j.sal.fs.exists('%s/%s' % (path, aysfile))]
            if exists:
                templ = ServiceTemplate(path, domain=domain)
                if templ.name in self._templates:
                    raise j.exceptions.Input("Found double template: %s"%template)
                self._templates[templ.name]=templ

        if not self._templates:
            self._doinit()

            for domain, domainpath in self.domains:
                # print "load template domain:%s"%domainpath
                load(domain, domainpath)

        return self._templates



    # @property
    # def roletemplates(self):
    #     if self._roletemplates:
    #         return self._roletemplates
    #     templatespaths = [j.sal.fs.joinPaths(self.basepath, '_templates')]
    #     for _, metapath in self._domains:
    #         templatespaths.append(j.sal.fs.joinPaths(metapath, '_templates'))
    #     templatespaths.reverse()

    #     for templatespath in templatespaths:
    #         if j.sal.fs.exists(templatespath):
    #             for roletemplate in j.sal.fs.listDirsInDir(templatespath):
    #                 paths = ['schema_tmpl.hrd', 'actions_tmpl_mgmt.py', 'actions_tmpl_node.py']
    #                 rtpaths = [path for path in paths if j.sal.fs.exists(j.sal.fs.joinPaths(templatespath, roletemplate, path))]
    #                 if rtpaths:
    #                     self._roletemplates[j.sal.fs.getBaseName(roletemplate)] = [j.sal.fs.joinPaths(roletemplate, rtpath) for rtpath in rtpaths]
    #     return self._roletemplates

    def _doinit(self):

        if self._init is False:

            # if we don't have write permissin on /opt don't try do download service templates
            opt = j.tools.path.get('/opt')
            if not opt.access(os.W_OK):
                self._init = True
                return

            # j.actions.reset()

            # j.do.debug=True

            if j.sal.fs.exists(path="/etc/my_init.d"):
                self.indocker=True

            # login=j.application.config.get("whoami.git.login").strip()
            # passwd=j.application.config.getStr("whoami.git.passwd").strip()

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


    def createAYSRepo(self, path):
        j.sal.fs.createDir(path)
        j.sal.fs.createEmptyFile(j.sal.fs.joinPaths(path, '.ays'))
        j.sal.fs.createDir(j.sal.fs.joinPaths(path, 'servicetemplates'))
        j.sal.fs.createDir(j.sal.fs.joinPaths(path, 'blueprints'))
        j.sal.process.execute("git init %s" % path, die=True, outputToStdout=False, useShell=False, ignoreErrorOutput=False)
        j.sal.nettools.download('https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore', j.sal.fs.joinPaths(path, '.gitignore'))
        name = j.sal.fs.getBaseName(path)
        self._repos[name] = AtYourServiceRepo(name, path)
        print("AYS Repo created at %s" % path)

    def updateTemplates(self, repos=[]):
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

    def getActionsBaseClassMgmt(self):
        return ActionsBaseMgmt

    def getActionMethodDecorator(self):
        return ActionMethodDecorator

    def getBlueprint(self,aysrepo,path):
        return Blueprint(aysrepo,path)

    # def getRoleTemplateClass(self, role, ttype):
    #     if role not in self.roletemplates:
    #         raise j.exceptions.RuntimeError('Role template %s does not exist' % role)
    #     roletemplatepaths = self.roletemplates[role]
    #     for roletemplatepath in roletemplatepaths:
    #         if ttype in j.sal.fs.getBaseName(roletemplatepath):
    #             modulename = "JumpScale.atyourservice.roletemplate.%s.%s" % (role, ttype)
    #             mod = loadmodule(modulename, roletemplatepath)
    #             return mod.Actions
    #     return None

    # def getRoleTemplateHRD(self, role):
    #     if role not in self.roletemplates:
    #         raise j.exceptions.RuntimeError('Role template %s does not exist' % role)
    #     roletemplatepaths = self.roletemplates[role]
    #     hrdpaths = [path for path in roletemplatepaths if j.sal.fs.getFileExtension(path) == 'hrd']
    #     if hrdpaths:
    #         hrd = j.data.hrd.getSchema(hrdpaths[0])
    #         for path in hrdpaths[1:]:
    #             hrdtemp = j.data.hrd.getSchema(path)
    #             hrd.items.update(hrdtemp.items)
    #         return hrd.hrdGet()
    #     return None


    def findTemplates(self, name="", domain="", role=''):
        res = []
        for template in self.templates:
            if not(name == "" or template.name == name):
                # no match continue
                continue
            if not(domain == "" or template.domain == domain):
                # no match continue
                continue
            if not (role == '' or template.role == role):
                # no match continue
                continue
            res.append(template)

        return res

    def findAYSRepos(self):
        return (root for root, dirs, files in os.walk(j.dirs.codeDir) if '.ays' in files)

    def getService(self,key,die=True):
        if key.count("!")!=2:
            raise j.exceptions.Input("key:%s needs to be $reponame!$role!$instance"%key)
        reponame,role,instance=key.split("!",2)
        if reponame not in self._repos:
            if die:
                raise j.exceptions.Input("service repo %s does not exist, could not retrieve ays service:%s"%(reponame,key))
            else:
                return None
        repo=self._repos[reponame]
        return repo.getService(role=role,instance=instance,die=die)

    def getTemplate(self,  name, die=True):
        """
        @param first means, will only return first found template instance
        """
        if name in self.templates:
            return self.templates[name]
        if die:
            raise j.exceptions.Input("Cannot find template with name:%s"%name)
        # if first:
        #     return self.findTemplates(domain=domain, name=name, version=version, role=role, first=first)
        # else:
        #     res = self.findTemplates(domain=domain, name=name, version=version, role=role, first=first)
        #     if len(res) > 1:
        #         if die:
        #             raise j.exceptions.Input("Cannot get ays template '%s|%s (%s)', found more than 1" % (domain, name, version), "ays.gettemplate")
        #         else:
        #             return
        #     if len(res) == 0:
        #         if die:
        #             raise j.exceptions.Input("Cannot get ays template '%s|%s (%s)', did not find" % (domain, name, version), "ays.gettemplate")
        #         else:
        #             return
        #     return res[0]

    def existsTemplate(self, name):
        if self.getTemplate(name,die=False)==None:
            return False
        return True

    def __str__(self):
        return self.__repr__()

    # def telegramBot(self, token, start=True):
    #     from JumpScale.baselib.atyourservice.telegrambot.TelegramAYS import TelegramAYS
    #     bot = TelegramAYS(token)
    #     if start:
    #         bot.run()
    #     return bot
