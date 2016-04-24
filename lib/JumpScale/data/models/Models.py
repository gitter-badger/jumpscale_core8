
from mongoengine.fields import IntField, StringField, ListField, BooleanField, DictField, EmbeddedDocumentField, FloatField
from mongoengine import DoesNotExist, EmbeddedDocument, Document
import crypt
import hmac
from JumpScale import j

DB = 'jumpscale_system'

default_meta = {'allow_inheritance': True, "db_alias": DB}

def extend(a, b):
    if isinstance(a, list):
        return a + b
    elif isinstance(a, dict):
        tmp = a.copy()
        for i in b:
            if not i in tmp:
                tmp[i] = b[i]
            else:
                tmp[i] = extend(tmp[i], b[i])
        return tmp
    else:
        return b

class ModelBase0():

    @property
    def guid(self):
        redis = getattr(self, '__redis__', False)
        if redis:
            if "_guid" in self.__dict__:
                return self._guid

            if "id" in self._fields and self.id!=None:
                self._guid=self.id
            elif "name" in self._fields and self.name!=None and self.name!="":
                self._guid=self.name
            else:
                self._guid=j.data.idgenerator.generateGUID()

        else:        
            return self.pk

    @guid.setter
    def guid(self, value):
        redis = getattr(self, '__redis__', False)
        if redis:
            self._guid=value
        else:
            self.pk = value

    def to_dict(self):
        self.guid
        d = j.data.serializer.json.loads(Document.to_json(self))
        if "_cls" in d:    
            d.pop("_cls")
        if "_id" in d:
            d.pop("_id")
        return d

    def to_wiki(self):
        ddict=self.to_dict()
        keys=[item for item in ddict.keys()]
        keys.sort()

        if "name" in keys:
            keys.pop("name")
            keys.insert(0,"name")

        if "id" in keys:
            keys.pop("id")
            keys.insert(0,"id")

    @classmethod
    def find(cls, query):
        redis = getattr(cls, '__redis__', False)
        if redis:
            raise j.exceptions.RuntimeError("not implemented")
        else:
            return cls.objects(__raw__=query)

    @classmethod
    def findByMethod(cls, method):
        """
        argument to method = the object
        when you want to return it, return True as result of the method

        e.g

        def mysearchMethod(obj):
            if obj.name=="myname":
                return True
            return False

        for item in ...findByMethod(mysearchMethod):
            print (item)

        """
        redis = getattr(cls, '__redis__', False)
        res=[]
        if redis:
            ttype = cls._class_name.split(".")[-1]
            key = "models.%s" % ttype
            for guid in j.core.db.hkeys(key):
                guid=guid.decode()
                obj=cls.get(guid)
                if method(obj):
                    res.append(obj)
            return res
        else:
            raise j.exceptions.RuntimeError("not implemented")

    @classmethod
    def list(cls):
        def all(o):
            return True
        return cls.findByMethod(all)

    @classmethod
    def redis_destroy(cls):
        """
        delete all items in redis
        """
        redis = getattr(cls, '__redis__', False)
        res=[]
        if redis:
            ttype = cls._class_name.split(".")[-1]
            key = "models.%s" % ttype
            j.core.db.delete(key)

    @property
    def hash(self):
        from IPython import embed
        print ("DEBUG NOW hash")
        embed()

    @classmethod
    def hashlist(cls):
        """
        get a dict which is guid,hash of obj
        """
        res = {}
        for item in cls.list():
            res[item.guid] = item.hash
        return res

    @classmethod
    def _getRedisKey(cls, guid):
        """
        @return hsetkey,key
        """
        ttype = cls._class_name.split(".")[-1]
        key = "models.%s" % ttype
        key = key.encode('utf-8')
        hkey = guid.encode('utf-8')
        return (key, hkey)

    @classmethod
    def get(cls, guid):
        """
        default needs to be in redis, need to mention if not
        """
        redis = getattr(cls, '__redis__', False)

        if redis:
            key, hkey = cls._getRedisKey(guid)
            modelraw = j.core.db.hget(key, hkey)
            if modelraw:
                modelraw = modelraw.decode()
                obj = cls.from_json(modelraw)
                return obj
            else:
                res = None
        else:
            try:
                res = cls.objects.get(id=guid)
            except DoesNotExist:
                res = None
        return res

    @classmethod
    def _save_redis(cls, obj):
        #leave next here to make sure it gets created
        obj.guid
        key,hkey = cls._getRedisKey(obj.guid)
        meta = cls._meta['indexes']
        # expire = meta[0].get('expireAfterSeconds', None) if meta else None
        #CANNOT WORK BECAUSE IS HSET, DO NOT CHANGE TO NON HSET
        raw = j.data.serializer.json.dumps(obj.to_dict())
        j.core.db.hset(key,hkey, raw)
        # if expire:
        #     j.core.db.expire(key, expire)
        return obj

    def validate(self, clean=True):        
        return Document.validate(self, clean)

    def _datatomodel(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def save(self, data=None):
        redis = getattr(self, '__redis__', False)
        if data:
            self._datatomodel(data)
        if redis:
            self.validate()
            return self._save_redis(self)
        else:
            return Document.save(self)

    def delete(self):
        redis = getattr(self, '__redis__', False)
        if redis:
            key = self._getRedisKey(self.guid)
            j.core.db.delete(key)
        else:
            return Document.delete(self)

    @classmethod
    def exists(cls, guid):
        redis = getattr(cls, '__redis__', False)
        if redis:
            key = cls._getRedisKey(cls.guid)
            model = cls.get(key)
            if model==None:
                return False
            else:
                return True
        else:
            return bool(cls.get(guid=guid))

    def getset(cls):
        redis = getattr(cls, '__redis__', False)
        if redis:
            key = cls._getRedisKey(cls.guid)
            model = cls.get(key)
            if model is None:
                model = cls.save()
            return model
        else:
            if not cls.get(cls.guid):
                cls.save()
            return cls.get(cls.guid)

    def __str__(self):
        return j.data.serializer.json.dumps(self.to_dict(), indent=2)

    __repr__ = __str__


class ModelBase(ModelBase0):
    DoesNotExist = DoesNotExist
    meta = default_meta    
    gid = IntField(default=lambda: j.application.whoAmI.gid if j.application.whoAmI else 0)
    nid = IntField(default=lambda: j.application.whoAmI.nid if j.application.whoAmI else 0)
    epoch = IntField(default=j.data.time.getTimeEpoch)

class Errorcondition(ModelBase, Document):
    nid = IntField(required=True)
    gid = IntField(required=True)
    aid = IntField(default=0)
    pid = IntField(default=0)
    jid = StringField(default='')  #@todo (*2*) is this right, string???
    masterjid = IntField(default=0)
    appname = StringField(default="")
    level = IntField(default=1, required=True)
    type = StringField(choices=("BUG", "PERF", "OPS", "UNKNOWN"), default="UNKNOWN", required=True)
    state = StringField(choices=("NEW", "ALERT", "CLOSED"), default="NEW", required=True)
    # StringField() <--- available starting version 0.9
    errormessage = StringField(default="")
    errormessagePub = StringField(default="")  # StringField()
    category = StringField(default="")
    tags = StringField(default="")
    code = StringField()
    funcname = StringField(default="")
    funcfilename = StringField(default="")
    funclinenr = IntField(default=0)
    backtrace = StringField()
    backtraceDetailed = StringField()
    extra = StringField()
    lasttime = IntField(default=j.data.time.getTimeEpoch())
    closetime = IntField(default=j.data.time.getTimeEpoch())
    occurrences = IntField(default=0)


class Log(ModelBase, Document):
    aid = IntField(default=0)
    pid = IntField(default=0)
    jid = StringField(default='')
    masterjid = IntField(default=0)
    appname = StringField(default="")
    level = IntField(default=1, required=True)
    message = StringField(default='')
    type = StringField(choices=("BUG", "PERF", "OPS", "UNKNOWN"), default="UNKNOWN", required=True)
    state = StringField(choices=("NEW", "ALERT", "CLOSED"), default="NEW", required=True)
    # StringField() <--- available starting version 0.9
    category = StringField(default="")
    tags = StringField(default="")
    epoch = IntField(default=j.data.time.getTimeEpoch())


class Grid(ModelBase, Document):
    name = StringField(default='master')
    #  id = IntField(default=1)


class Group(ModelBase, Document):
    name = StringField(default='')
    domain = StringField(default='')
    gid = IntField(default=1)
    roles = ListField(StringField())
    active = BooleanField(default=True)
    description = StringField(default='master')
    lastcheck = IntField(default=j.data.time.getTimeEpoch())


class Job(EmbeddedDocument):
    nid = IntField(required=True)
    gid = IntField(required=True)
    data = StringField(default='')
    streams = ListField(StringField())
    level = IntField()
    state = StringField(required=True, choices=('SUCCESS', 'ERROR', 'TIMEOUT', 'KILLED', 'QUEUED', 'RUNNING'))
    starttime = IntField()
    time = IntField()
    tags = StringField()
    critical = StringField()

    meta = extend(default_meta, {
        'indexes': [{'fields': ['epoch'], 'expireAfterSeconds': 3600 * 24 * 5}],
        'allow_inheritance': True,
        "db_alias": DB
    })


class Command(ModelBase, Document):
    guid = StringField(unique=True, required=True)
    gid = IntField(default=0)
    nid = IntField(default=0)
    cmd = StringField()
    roles = ListField(StringField())
    fanout = BooleanField(default=False)
    args = DictField()
    data = StringField()
    tags = StringField()
    starttime = IntField()
    jobs = ListField(EmbeddedDocumentField(Job))

    meta = extend(default_meta, {
        'indexes': [{'fields': ['guid']}]
    })


class Audit(ModelBase, Document):
    user = StringField(default='')
    result = StringField(default='')
    call = StringField(default='')
    status_code = IntField(default=0)
    args = StringField(default='')
    kwargs = StringField(default='')
    timestamp = IntField(default=j.data.time.getTimeEpoch())

    meta = extend(default_meta, {'indexes': [
        {'fields': ['epoch'], 'expireAfterSeconds': 3600 * 24 * 5}
    ], 'allow_inheritance': True, "db_alias": DB})

class Disk(ModelBase, Document):
    partnr = IntField()
    path = StringField(default='')
    size = IntField(default=0)
    free = IntField()
    ssd = IntField()
    fs = StringField(default='')
    mounted = BooleanField()
    mountpoint = StringField(default='')
    active = BooleanField()
    model = StringField(default='')
    description = StringField(default='')
    type = ListField(StringField())  # BOOT, DATA, ...
    # epoch of last time the info was checked from reality
    lastcheck = IntField(default=j.data.time.getTimeEpoch())


class VDisk(ModelBase, Document):

    machineguid = StringField(required=True)
    diskid = IntField()
    fs = StringField(default='')
    size = IntField(default=0)
    free = IntField()
    sizeondisk = IntField()
    mounted = BooleanField()
    path = StringField(default='')
    description = StringField(default='')
    mountpoint = StringField(default='')
    role = ListField(StringField())
    type = ListField(StringField())
    order = IntField()
    devicename = StringField(default='') #if known device name in vmachine
    lastcheck = IntField(default=j.data.time.getTimeEpoch())
    backup = BooleanField()
    backuplocation = StringField()
    backuptime  = IntField(default=j.data.time.getTimeEpoch())
    backupexpiration = IntField()

class Alert(ModelBase, Document):
    username = StringField(default='')
    description = StringField(default='')
    descriptionpub = StringField(default='')
    level = IntField(min_value=1, max_value=3, default=1)
    # dot notation e.g. machine.start.failed
    category = StringField(default='')
    tags = StringField(default='')  # e.g. machine:2323
    state = StringField(choices=("NEW","ALERT","CLOSED"), default='NEW', required=True)
    history = ListField(DictField())
    # first time there was an error condition linked to this alert
    inittime = IntField(default=j.data.time.getTimeEpoch())
    # last time there was an error condition linked to this alert
    lasttime = IntField()
    closetime = IntField()  # alert is closed, no longer active
    # $nr of times this error condition happened
    nrerrorconditions = IntField()
    errorconditions = ListField(IntField())  # ids of errorconditions


class Heartbeat(ModelBase, Document):

    """
    """
    lastcheck = IntField(default=j.data.time.getTimeEpoch())


class Machine(ModelBase, Document):
    name = StringField(default='')
    roles = ListField(StringField())
    netaddr = StringField(default='')
    ipaddr = ListField(StringField())
    active = BooleanField()
    # STARTED,STOPPED,RUNNING,FROZEN,CONFIGURED,DELETED
    state = StringField(choices=("STARTED","STOPPED","RUNNING","FROZEN","CONFIGURED","DELETED"), default='CONFIGURED', required=True)
    mem = IntField()  # $in MB
    cpucore = IntField()
    description = StringField(default='')
    otherid = StringField(default='')
    type = StringField(default='')  # VM,LXC
    # epoch of last time the info was checked from reality
    lastcheck = IntField(default=j.data.time.getTimeEpoch())


class Nic(ModelBase, Document):
    name = StringField(default='')
    mac = StringField(default='')
    ipaddr = ListField(StringField())
    active = BooleanField(default=True)
    # poch of last time the info was checked from reality
    lastcheck = IntField(default=j.data.time.getTimeEpoch())


class Node(ModelBase, Document):
    name = StringField(default='')
    roles = ListField(StringField())
    netaddr = DictField(default={})
    machineguid = StringField(default='')
    ipaddr = ListField(StringField())
    active = BooleanField()
    peer_stats = IntField()  # node which has stats for this node
    # node which has transactionlog or other logs for this node
    peer_log = IntField()
    peer_backup = IntField()  # node which has backups for this node
    description = StringField(default='')
    lastcheck = IntField(default=j.data.time.getTimeEpoch())
    # osisrootobj,$namespace,$category,$version
    _meta = ListField(StringField())


class Process(ModelBase, Document):
    aysdomain = StringField(default='')
    aysname = StringField(default='')
    pname = StringField(default='')  # process name
    sname = StringField(default='')  # name as specified in startup manager
    ports = ListField(IntField())
    instance = StringField(default='')
    systempid = ListField(IntField())  # system process id (PID) at this point
    epochstart = IntField()
    epochstop = IntField()
    active = BooleanField()
    lastcheck = IntField(default=j.data.time.getTimeEpoch())
    cmd = StringField(default='')
    workingdir = StringField(default='')
    parent = StringField(default='')
    type = StringField(default='')
    statkey = StringField(default='')
    nr_file_descriptors = FloatField()
    nr_ctx_switches_voluntary = FloatField()
    nr_ctx_switches_involuntary = FloatField()
    nr_threads = FloatField()
    cpu_time_user = FloatField()
    cpu_time_system = FloatField()
    cpu_percent = FloatField()
    mem_vms = FloatField()
    mem_rss = FloatField()
    io_read_count = FloatField()
    io_write_count = FloatField()
    io_read_bytes = FloatField()
    io_write_bytes = FloatField()
    nr_connections_in = FloatField()
    nr_connections_out = FloatField()


class Test(ModelBase, Document):
    name = StringField(default='')
    testrun = StringField(default='')
    path = StringField(default='')
    state = StringField(choices=("OK", "ERROR", "DISABLED"), default='OK', required=True)
    priority = IntField()  # lower is highest priority
    organization = StringField(default='')
    author = StringField(default='')
    version = IntField()
    categories = ListField(StringField())
    starttime = IntField(default=j.data.time.getTimeEpoch())
    endtime = IntField()
    enable = BooleanField()
    result = DictField()
    output = DictField(default={})
    eco = DictField(default={})
    license = StringField(default='')
    source = DictField(default={})


class User(ModelBase, Document):
    name = StringField(default='')
    domain = StringField(default='')
    passwd = StringField(default='')  # stored hashed
    roles = ListField(StringField())
    active = BooleanField()
    description = StringField(default='')
    emails = ListField(StringField())
    xmpp = ListField(StringField())
    mobile = ListField(StringField())
    # epoch of last time the info updated
    lastcheck = IntField(default=j.data.time.getTimeEpoch())
    groups = ListField(StringField())
    authkey = StringField(default='')
    data = StringField(default='')
    authkeys = ListField(StringField())

    def authenticate(username, passwd):
        for user in User.find({'name': username}):
            if hmac.compare_digest(user.passwd, crypt.crypt(passwd, user.passwd)):
                return True
        return False

    def save(user):
        if not user.id:
            user.passwd = crypt.crypt(user.passwd)
        else:
            olduser = User.get(user.id)
            if olduser.passwd != user.passwd:  # change passwd
                user.passwd = crypt.crypt(user.passwd)
        super(ModelBase, user).save()


class SessionCache(ModelBase, Document):
    __redis__ = True

    user = StringField()
    _creation_time = IntField(default=j.data.time.getTimeEpoch())
    _accessed_time = IntField(default=j.data.time.getTimeEpoch())
    guid = StringField()
    meta = extend(default_meta, {'indexes': [
        {'fields': ['epoch'], 'expireAfterSeconds': 432000}
    ], 'allow_inheritance': True, "db_alias": DB})

del EmbeddedDocument