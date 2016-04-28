

from JumpScale import j
import imp
import sys
import os

# import JumpScale.tools.actions

from Service import *

# from ServiceTemplateBuilder import *


# def loadmodule(name, path):
#     parentname = ".".join(name.split(".")[:-1])
#     sys.modules[parentname] = __package__
#     mod = imp.load_source(name, path)
#     return mod


class ServiceTemplate(object):

    def __init__(self, path,domain=""):
        self.path = path

        base = j.sal.fs.getBaseName(path)

        _, self.name, self.version, _, _ = j.atyourservice.parseKey(base)
        if base.find("__") != -1:
            self.domain, self.name = base.split("__", 1)
        else:
            self.domain = domain

        self._init()
        self.key = j.atyourservice.getKey(self)

        self.fix()

    def fix(self):
        if j.sal.fs.exists(j.sal.fs.joinPaths(self.path, "actions_mgmt.py")):
            j.sal.fs.renameFile(j.sal.fs.joinPaths(self.path, "actions_mgmt.py"),self.path_actions)                

    def _init(self):
        self.path_hrd_template = j.sal.fs.joinPaths(self.path, "service.hrd")
        self.path_hrd_schema = j.sal.fs.joinPaths(self.path, "schema.hrd")
        self.path_actions = j.sal.fs.joinPaths(self.path, "actions.py")
        self.path_actions_node = j.sal.fs.joinPaths(self.path, "actions_node.py")
        self.path_mongo_model = j.sal.fs.joinPaths(self.path, "model.py")

        self.role = self.name.split('.')[0]

        self._hrd = None
        self._schema = None
        self._actions = None
        self._mongoModel = None

    @property
    def hrd(self):
        if self._hrd:
            return self._hrd
        hrdpath = self.path_hrd_template
        if not j.sal.fs.exists(hrdpath):
            # check if we can find it in other ays template
            if self.name.find(".") != -1:
                role = self.name.split(".", 1)[0]
                templ = j.atyourservice.getTemplate(domain=self.domain, role=role, die=False)
                if templ is not None:
                    self._hrd = templ._hrd or j.data.hrd.get(content="")
                    self.path_hrd_template = templ.path_hrd_template
                    return self._hrd
            self._hrd=j.data.hrd.get(content="")
            # raise j.exceptions.OPERATIONS(msg="can't find %s." % hrdpath, category="ays load hrd template")
        else:
            self._hrd = j.data.hrd.get(hrdpath, prefixWithName=False)
        return self._hrd

    @property
    def schema(self):
        if self._schema:
            return self._schema
        hrdpath = self.path_hrd_schema
        if not j.sal.fs.exists(hrdpath):
            j.sal.fs.touch(hrdpath)
        self._schema = j.data.hrd.getSchema(hrdpath)
        return self._schema


    @property
    def model(self):
        if self._mongoModel is None:
            if j.sal.fs.exists(self.path_mongo_model):
                modulename = "JumpScale.atyourservice.%s.%s.model" % (self.domain, self.name)
                mod = loadmodule(modulename, self.path_mongo_model)
                self._mongoModel = mod.Model()
        return self._mongoModel


    @property
    def recipe(self):
        from ServiceRecipe import ServiceRecipe
        return ServiceRecipe(template=self)

    def __repr__(self):
        return "template: %-15s:%s (%s)" % (self.domain, self.name,self.version)

    def __str__(self):
        return self.__repr__()
