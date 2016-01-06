from JumpScale import j
# import JumpScale.baselib.codeexecutor
from HRD import HRD
from HRDTree import HRDTree
from HRDSchema import HRDSchema

class HRDFactory:
    def __init__(self):
        self.__jslocation__="j.data.hrd"
        self.logenable=False
        self.loglevel=5

    def log(self,msg,category="",level=5):
        # if "logger" not in j.__dict__:
        #     print(msg)
        if level<self.loglevel+1 and self.logenable:
            j.logger.log(msg,category="hrd.%s"%category,level=level)

    def getSchema(self,path=None,content=""):
        if path!=None:
            content=j.do.readFile(path)
        if content=="":
            j.events.inputerror_critical("Content needs to be provided if path is empty")
        return HRDSchema(content)

    def get(self,path=None,content="",prefixWithName=True,keepformat=False,args={},templates=[]):
        """
        @param path
        """        
        if templates=="":
            templates=[]
        if path is not None and j.sal.fs.isDir(path):
            if content!="":
                j.events.inputerror_critical("HRD of directory cannot be build with as input content (should be empty)")
            return HRDTree(path,prefixWithName=prefixWithName,keepformat=keepformat)
        else:
            return HRD(path=path,content=content,prefixWithName=prefixWithName,keepformat=keepformat,args=args,templates=templates)


    def getHRDFromMongoObject(self, mongoObject, prefixRootObjectType=True):
        txt = j.data.serializer.serializers.hrd.dumps(mongoObject.to_dict())
        prefix = mongoObject._P__meta[2]
        out=""
        for line in txt.split("\n"):
            if line.strip()=="":
                continue
            if line[0]=="_":
                continue
            if line.find("_meta.")!=-1:
                continue
            if prefixRootObjectType:
                out+="%s.%s\n"%(prefix,line)
            else:
                out+="%s\n"%(line)
        return self.getHRDFromContent(out)   


    def getHRDFromDict(self,ddict={}):
        hrd=self.get(content=" ",prefixWithName=False)
        for key,val in ddict.items():
            hrd.set(key,val)  
        return hrd
