from JumpScale import j

import Models
import inspect

try:
    import mongoengine
except:
    pass


class NameSpaceLoader():
    def __init__(self, modelsmodule):
        self._module = modelsmodule
        mongoengine.register_connection(self._module.DB, self._module.DB) #@todo why is this? (despiegk)
        self._getModels()

    def _getModels(self):
        self._models = list()
        self._modelspecs = dict()
        for name, mem in inspect.getmembers(self._module, inspect.isclass):
            if issubclass(mem, mongoengine.base.document.BaseDocument) and mongoengine.Document != inspect.getmro(mem)[0]:
                self._models.append(name)
                self._modelspecs[name] = mem
                self.__dict__[name] = mem

    def addModel(self, modelclass):
        self._models.append(modelclass._class_name)
        self._modelspecs[modelclass._class_name] = modelclass
        self.__dict__[modelclass._class_name] = modelclass

    def listModels(self):
        return self._models

    def connect2mongo(self, host='localhost', port=27017, db='jumpscale_system'):
        """
        """
        mongoengine.connect(db=db, alias=db, host=host, port=port)


class NameSpace():
    def __init__(self,name):
        mongoengine.register_connection(name,name)
        self._name=name
        self._models = list()
        self._modelspecs = dict()        

    def addModel(self, modelclass,redis=None,mongo=None):
        self._models.append(modelclass._class_name)
        self._modelspecs[modelclass._class_name] = modelclass
        self.__dict__[modelclass._class_name] = modelclass
        if redis!=None:
            self.__dict__[modelclass._class_name].__redis__=redis


    def listModels(self):
        return self._models

    def connect2mongo(self, host='localhost', port=27017, db='jumpscale_system'):
        """
        """
        mongoengine.connect(db=db, alias=db, host=host, port=port)

class BaseModelFactory():
    def __init__(self):
        self.__jslocation__ = "j.data.models"
        self._system=None

    def getModelBaseClass(self):
        return Models.ModelBase0

    # def connect2mongo(self, host='localhost', port=27017, db='jumpscale_system'):
    #     """
    #     """
    #     mongoengine.connect(db=db, alias=db, host=host, port=port)        

    def addModel(self,namespaceName,modelclass,redis=j.core.db,mongo=None):
        """
        e.g. 

        from mongoengine.fields import *
        from mongoengine import DoesNotExist, EmbeddedDocument, Document

        ModelBase=j.data.models.getModelBaseClass()

        class Repository(ModelBase, Document):
            id = IntField(required=True)
            name = StringField(default='')

        j.data.models.addModule("github",Repository,redis=j.core.db) 

        #if you want to use mongodb 
        #j.data.models.addModule("github",Repository,mongo=...) 

        #now we can use the model as follows

        repoEmptyObj=j.data.models.github.Repository()
        repoEmptyObj.id=1
        repoEmptyObj.name="test"

        repoEmptyObj.save()

        repoEmptyObj2=j.data.models.github.Repository()
        repoEmptyObj.id=2
        repoEmptyObj2.name="test2"
        repoEmptyObj2.save()

        print (repoEmptyObj2)

        """
        if mongo!=None:
            raise RuntimeError("not implemented") #@todo

        if not hasattr(self,namespaceName):
            self.__dict__[namespaceName]=NameSpace(namespaceName)

        ns=self.__dict__[namespaceName]
        ns.addModel(modelclass,redis=redis,mongo=mongo)


    @property
    def system(self):
        if self._system==None:
            self._system=NameSpaceLoader(Models)
        return self._system
        
    
