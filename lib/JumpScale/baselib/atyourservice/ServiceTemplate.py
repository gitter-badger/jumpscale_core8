

from JumpScale import j

from Service import *
from ServiceRecipe import *


class ServiceTemplate(object):

    def __init__(self, path, domain=""):
        self.path = path

        base = j.sal.fs.getBaseName(path)
        self.name=base
        
        if base.find("__") != -1:
            self.domain, self.name = base.split("__", 1)
        else:
            self.domain = domain

        self._init_props()

    def _init_props(self):
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
        if self._hrd == "EMPTY":
            return None
        if self._hrd is not None:
            return self._hrd
        hrdpath = self.path_hrd_template
        if not j.sal.fs.exists(hrdpath):
            # check if we can find it in other ays template
            if self.name.find(".") != -1:
                name0 = self.name.split(".", 1)[0]
                templ = j.atyourservice.getTemplate(name=name0, die=False)
                if templ is not None:
                    self._hrd = templ._hrd
                    self.path_hrd_template = templ.path_hrd_template
                    return self._hrd
                else:
                    self._hrd == "EMPTY"
                    return None
        if j.sal.fs.exists(hrdpath):
            self._hrd = j.data.hrd.get(hrdpath, prefixWithName=False)
        else:
            self._hrd = "EMPTY"
            return None
        return self._hrd

    @property
    def schema(self):
        if self._schema == "EMPTY":
            return None
        if self._schema:
            return self._schema
        hrdpath = self.path_hrd_schema
        if not j.sal.fs.exists(hrdpath):
            self._schema = "EMPTY"
            return None
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

    def getRecipe(self, aysrepo):
        from ServiceRecipe import ServiceRecipe
        return ServiceRecipe(aysrepo, template=self)

    def __repr__(self):
        return "template: %-15s:%s" % (self.domain, self.name)

    def __str__(self):
        return self.__repr__()
