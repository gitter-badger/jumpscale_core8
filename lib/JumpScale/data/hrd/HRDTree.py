from JumpScale import j
# import JumpScale.baselib.codeexecutor

from HRDBase import HRDBase

from HRD import HRD


class HRDTree(HRDBase):
    def __init__(self,path="",prefixWithName=False,keepformat=True):
        self.items={} #link between key & hrd storing the key
        self.hrds=[] #all hrd's in tree
        self.changed=False
        self.commentblock=""
        self.name="tree"
        self.path="tree"
        self.prefixWithName=prefixWithName
        self.keepformat=keepformat
        if path!="":
            self.add2tree(path)

    def add2treeFromContent(self,content):
        hrd=HRD("",treeposition,self,prefixWithName=self.prefixWithName,keepformat=self.keepformat)
        self.hrds.append(hrd)
        hrdpos=len(self.hrds)-1
        hrd.process(content)

    def add2tree(self,path,recursive=True):
        paths= j.sal.fs.listFilesInDir(path, recursive=True, filter="*.hrd")

        for pathfound in paths:
            j.data.hrd.logger.info("Add hrd %s" % (pathfound))
            hrd=HRD(pathfound,self,prefixWithName=self.prefixWithName,keepformat=self.keepformat)
            self.hrds.append(hrd)

    def getHrd(self,key):
        if key not in self.items:
            raise j.exceptions.Input("Cannot find key:'%s' in tree"%key,"hrdtree.gethrd.notfound")
        return self.items[key].hrd

    def set(self,key,val,persistent=True):
        hrd=self.getHrd(key)
        hrd.set(key,val,persistent=persistent)

    def delete(self,key):
        hrd=self.getHrd(key)
        hrd.delete(key)

    def get(self,key,default=None,):
        if key not in self.items:
            if default==None:
                raise j.exceptions.Input("Cannot find value with key %s in tree %s."%(key,self.path),"hrd.get.notexist")
            val=default
        else:
            val= self.items[key].get()
        j.data.hrd.logger.info("hrd get '%s':'%s'"%(key,val))
        return val
