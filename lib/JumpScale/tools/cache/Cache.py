from JumpScale import j

try:
    import ujson as json
except:
    import json

class CacheFactory():
    def __init__(self):
        self.__jslocation__ = "j.tools.cache"

    def get(self,db,expiration=300):
        """
        db is keyvalue stor to use
        e.g. j.db.cache.get(j.db.keyvaluestore.getRedisStore(namespace="cache"))
        """
        return Cache(db,expiration)


class Cache():

    def __init__(self, db,expiration=300):
        self.db=db
        self.expiration=expiration
        self.redis=str(self.db).find("redis")!=-1

    def set(self,key,value):
        tostore={}
        tostore["val"]=value
        tostore["expire"]=j.data.time.getTimeEpoch()+self.expiration
        data=json.dumps(tostore)
        if self.redis:
            self.db.set("cache", key, data)
        else:
            self.db.set("cache", key, data,expire=self.expiration)

    def get(self,key):
        """
        expire = bool, is true if expired
        return (expire,value)
        """
        data=self.db.get("cache", key)
        if data==None:
            return False,None
        data=json.loads(data)
        if data["expire"]<j.base.time.getTimeEpoch():
            self.db.delete("cache", key)
            return (True,data["val"])
        else:
            return (False,data["val"])

    def delete(self,key):
        data=self.db.delete("cache", key)
