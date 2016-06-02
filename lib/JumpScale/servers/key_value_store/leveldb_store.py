from JumpScale import j
from servers.key_value_store.store import KeyValueStoreBase


import plyvel

class LevelDBInterface:

    def __init__(self,namespace,basedir):
        j.sal.fs.createDir(basedir)
        self.path="%s/%s"%(basedir,namespace)
        self.db=plyvel.DB(self.path, create_if_missing=True, compression='snappy', bloom_filter_bits=10,lru_cache_size=100*1024*1024,write_buffer_size=1*1024*1024)
        #write_buffer_size=None, max_open_files=None, lru_cache_size=None, block_size=None, block_restart_interval=None

    def repair(self):
        plyvel.repair_db()#paranoid_checks=None, write_buffer_size=None, max_open_files=None, lru_cache_size=None, block_size=None, block_restart_interval=None, compression='snappy', bloom_filter_bits=0 )

    def setb(self,key,value):
        # print "setb:%s"%key
        self.db.put(key,value,sync=False)

    def set(self,key,value):
        # print "set:%s"%key
        val=j.data.serializer.serializers.getSerializerType('j').dumps(value)
        self.setb(key,val)

    def getb(self,key):
        result= self.db.get(key,fill_cache=True,verify_checksums=True)
        if result==None:
            raise j.exceptions.RuntimeError("Cannot find object in db with key:%s"%key)
        return result

    def get(self,key):
        value=self.getb(key)        
        if value==None:
            raise j.exceptions.RuntimeError("Cannot find object in db with key:%s"%key)
        val=j.data.serializer.serializers.getSerializerType('j').loads(value)
        return val

    def exists(self,key):
        val=self.db.get(key,default="NOTFOUND")
        return val!="NOTFOUND"

    def delete(self,key):
        self.db.delete(key)#,sync=False)

    def prefix(self,prefix):
        """
        """
        result=[]
        for key, value in self.db.iterator(prefix=prefix):
            result.append(key)


class LevelDBKeyValueStore(KeyValueStoreBase):

    def __init__(self, namespace=None,basedir="", serializers=None):
        KeyValueStoreBase.__init__(self, serializers)
        self.dbclient = LevelDBInterface(namespace,basedir)
        self.categories = dict()
        if not self.exists("dbsystem", "categories"):
            key=self._getCategoryKey("dbsystem", "categories")
            self.dbclient.set(key, {})
        self.categories=self.get("dbsystem", "categories")

    def getb(self, category, key):
        #self._assertExists(category, key)
        categoryKey = self._getCategoryKey(category, key)
        value = self.dbclient.getb(categoryKey)
        return value

    def setb(self, category, key, value, JSModelSerializer=None):
        if category not in self.categories:
            self.categories[category]=True
            self.set("dbsystem", "categories", self.categories)
        categoryKey = self._getCategoryKey(category, key)
        self.dbclient.setb(categoryKey, self.serialize(value))

    def get(self, category, key):
        categoryKey = self._getCategoryKey(category, key)
        value = self.dbclient.get(categoryKey)
        return self.unserialize(value)

    def set(self, category, key, value, JSModelSerializer=None):
        if category not in self.categories:
            self.categories[category]=True
            self.set("dbsystem", "categories", self.categories)
        categoryKey = self._getCategoryKey(category, key)
        #create transactionlog
        self.dbclient.set(categoryKey, self.serialize(value))

    def delete(self, category, key):
        categoryKey = self._getCategoryKey(category, key)
        self.dbclient.delete(categoryKey)

    def exists(self, category, key):
        categoryKey = self._getCategoryKey(category, key)
        return self.dbclient.exists(categoryKey)

    def list(self, category, prefix):
        categoryKey = self._getCategoryKey(category, prefix)
        fullKeys = self.dbclient.prefix(categoryKey)
        if fullKeys==None:
            return []
        # from IPython import embed
        # print "DEBUG NOW list"
        # embed()
        
        return self._stripCategory(fullKeys, category)

    def increment(self, incrementtype):
        """
        @param incrementtype : type of increment is in style machine.disk.nrdisk  (dot notation)
        """
        client = self.dbclient
        key = self._getCategoryKey("increment", incrementtype)
        if not client.exists(key):
            client.set(key, "1")
            incr=1
        else:
            rawOldIncr = client.get(key)
            if not rawOldIncr.isdigit():
                raise ValueError("Increment type %s does not have a digit value: %s" % (incrementtype, rawOldIncr))
            while True:
                oldIncr = int(rawOldIncr)
                incr = oldIncr + 1
                oldval = client.testAndSet(key, rawOldIncr, str(incr))
                if oldval == rawOldIncr:
                    break
                rawOldIncr = oldval
        return incr

    def listCategories(self):
        return list(self.categories.keys())

    def _stripKey(self, catKey):
        if "." not in catKey:
            raise ValueError("Could not find the category separator in %s" %catKey)
        return catKey.split(".", 1)[0]

    def _getCategoryKey(self, category, key):
        return str('%s.%s' % (category, key))

    def _stripCategory(self, keys, category):
        prefix = category + "."
        nChars = len(prefix)
        return [key[nChars:] for key in keys]

    def _categoryExists(self, category):
        categoryKey = self._getCategoryKey(category, "")
        return bool(self.dbclient.prefix(categoryKey, 1))
