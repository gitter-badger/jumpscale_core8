from JumpScale import j
from servers.serverbase.Exceptions import AuthenticationError, MethodNotFoundException, RemoteException
from servers.serverbase import returnCodes
import time
import uuid
from random import randrange

class Session:

    def __init__(self, id, organization, user, passwd, encrkey, netinfo, roles):
        self.id = id #is unique session id
        self.gid=j.application.whoAmI.gid
        self.nid=j.application.whoAmI.nid
        self.encrkey = encrkey
        self.user = user
        self.passwd = passwd
        self.organization = organization
        self.netinfo = netinfo
        self.start = int(time.time())
        self.roles = roles

    def __repr__(self):
        return str(self.__dict__)

    __str__ = __repr__


class SimpleClient:
    def __init__(self, client):
        self._client = client


class DaemonClient:

    def __init__(self, org="myorg", user="root", passwd="passwd", ssl=False, encrkey="", reset=False, roles=[], \
        transport=None, defaultSerialization="j",id=None):
        """
        @param encrkey (use for simple blowfish shared key encryption, better to use SSL though, will do the same but dynamically exchange the keys)
        """
        if id!=None:
            self._id=id
        else:
            end = 4294967295  # 4bytes max nr
            random = uuid.uuid4()
            self._id="%s_%s_%s_%s"%(j.application.whoAmI.gid,j.application.whoAmI.nid,j.application.whoAmI.pid, random)

        self.retry = True
        self.blocksize = 8 * 1024 * 1024
        self.key = encrkey
        self.user = user
        self.org = org
        self.passwd = passwd
        self.ssl = ssl

        if roles==[] and j.application.config.exists("grid.node.roles"):
            roles=j.application.config.get("grid.node.roles")
            roles=[item.strip().lower() for item in roles]

        # WARNING: Do not put this back this makes it impossible to register a node
        #if j.application.whoAmI.gid==0 or j.application.whoAmI.nid==0:
        #    raise j.exceptions.RuntimeError("gid or nid cannot be 0, see grid.hrd file in main config of jumpscale hrd dir")

        #WILL NOT LONGER ADD GID & NID
        # roles2=[]
        # for role in roles:
        #     role+=".%s.%s"%(j.application.whoAmI.gid,j.application.whoAmI.nid)
        #     roles2.append(role)

        self.roles = roles
        self.keystor = None
        self.key = None
        self.transport = transport
        self.pubkeyserver = None
        self.defaultSerialization = defaultSerialization
        self.transport.connect(self._id)
        #print("transport ok")
        self.initSession(reset, ssl)
        #print("init session")

    def encrypt(self, message):
        if self.ssl:
            if not self.pubkeyserver:
                self.pubkeyserver = self.sendcmd(category="core", cmd="getpubkeyserver")
            return self.keystor.encrypt(self.org, self.user, "", "", message=message, sign=True, base64=True, pubkeyReader=self.pubkeyserver)
        return message

    def decrypt(self, message):
        if self.ssl and self.key:
            return self.keystor.decrypt("", "", self.org, self.user, message)
        else:
            return message

    def initSession(self, reset=False, ssl=False):
        # print("initsession")
        if ssl:
            self.keystor = j.sal.ssl.getSSLHandler()
            try:
                publickey = self.keystor.getPubKey(self.org, self.user, returnAsString=True)
            except:
                # priv key now known yet
                reset = True

            if reset:
                publickey, _ = self.keystor.createKeyPair(organization=self.org, user=self.user)

            self.sendcmd(category="core", cmd="registerpubkey", organization=self.org, user=self.user, pubkey=publickey)

            # generate unique key
            encrkey = ""
            for i in range(56):
                encrkey += chr(randrange(0, 256))

            # only encrypt the key & the passwd, the rest is not needed
            encrkey = self.encrypt(encrkey)
            passwd = self.encrypt(self.passwd)

        else:
            encrkey = ""
            publickey = ""
            passwd = self.passwd

        session = Session(id=self._id, organization=self.org, user=self.user, passwd=passwd,
                          encrkey=encrkey, netinfo=j.sal.nettools.getNetworkInfo(), roles=self.roles)
        # ser=j.data.serializer.serializers.getMessagePack()
        # sessiondictstr=ser.dumps(session.__dict__)
        self.key = session.encrkey
        self.sendcmd(category="core", cmd="registersession", sessiondata=session.__dict__, ssl=ssl, returnformat="")
        #print("registered session")

    def sendMsgOverCMDChannel(self, cmd, data,sendformat=None, returnformat=None, retry=0, maxretry=2, \
        category=None,transporttimeout=5):
        """
        cmd is command on server (is asci text)
        data is any to be serialized data

        formatstring is right order of formats e.g. mc means messagepack & then compress
        formats see: j.data.serializer.serializers.get(?

        return is always multipart message [$resultcode(0=no error,1=autherror),$formatstr,$data]

        """
        ##LOGGING FOR DEBUG
        # try:
        #     dest=self.transport.url
        # except:
        #     dest="unknown"
        # print "###data send to %s\n%s\n#######"%(dest,data)
        
        if sendformat == None:
            sendformat = self.defaultSerialization
        if returnformat == None:
            returnformat = self.defaultSerialization
        rawdata = data
        if sendformat != "":
            ser = j.data.serializer.serializers.get(sendformat, key=self.key)
            data = ser.dumps(data)
        
        # data = data.decode('utf-8', 'replace')
        # self.cmdchannel.send_multipart([cmd,sendformat,returnformat,data])
        returncode, rreturnformat, returndata = self.transport.sendMsg(category, cmd, data, sendformat, returnformat,timeout=transporttimeout)
        # print "return:%s"%returncode
        if returncode == returnCodes.AUTHERROR:
            if retry < maxretry:
                #print("session lost")
                self.initSession()
                retry += 1
                return self.sendMsgOverCMDChannel(cmd, rawdata, sendformat=sendformat, returnformat=returnformat, retry=retry, maxretry=maxretry, category=category,transporttimeout=transporttimeout)
            else:
                msg = "Authentication error on server.\n"
                raise AuthenticationError(msg)
        elif returncode == returnCodes.METHOD_NOT_FOUND:
            msg = "Execution error on %s.\n Could not find method:%s\n" % (self.transport, cmd)
            raise MethodNotFoundException(msg)
        if str(returncode) != returnCodes.OK:
            # if isinstance(rreturnformat, bytes):
            #     rreturnformat = rreturnformat.decode('utf-8', 'ignore')
            s = j.data.serializer.serializers.get(rreturnformat)
            # print "*** error in client to zdaemon ***"
            ecodict = s.loads(returndata)
            if cmd == "logeco":
                raise j.exceptions.RuntimeError("Could not forward errorcondition object to logserver, error was %s" % ecodict)
            # for k, v in list(ecodict.items()):
            #     if isinstance(k, bytes):
            #         ecodict.pop(k)
            #         k = k.decode('utf-8', 'ignore')
            #     if isinstance(v, bytes):
            #         v = v.decode('utf-8', 'ignore')
            #     ecodict[k] = v
            if ecodict.get("errormessage").find("Authentication error")!=-1:
                raise AuthenticationError("Could not authenticate to %s for user:%s"%(self.transport,self.user), ecodict)
            raise RemoteException("Cannot execute cmd:%s/%s on server:'%s:%s' error:'%s' ((ECOID:%s))" %(category,cmd,ecodict["gid"],ecodict["nid"],ecodict["errormessage"],ecodict["guid"]), ecodict)

        if returnformat != "":
            # if isinstance(rreturnformat, bytes):
            #     rreturnformat = rreturnformat.decode('utf-8', 'ignore')
            ser = j.data.serializer.serializers.get(rreturnformat, key=self.key)
            res = self.decrypt(returndata)
            result = ser.loads(res)
        else:
            result = returndata

        return result

    def reset(self):
        # Socket is confused. Close and remove it.
        self.transport.close()
        self.transport.connect(self._id)


    def getCmdClient(self, category,sendformat="j", returnformat="j"):
        if category == "*":
            categories = self.sendcmd(category='core', cmd='listCategories')
            cl = SimpleClient(self)
            for category in categories:
                setattr(cl, category, self._getCmdClient(category))
            return cl
        else:
            return self._getCmdClient(category,sendformat,returnformat)


    def _getCmdClient(self, category,sendformat="j", returnformat="j"):
        client = SimpleClient(self)
        methodspecs = self.sendcmd(category='core', cmd='introspect', cat=category)
        for key, spec in list(methodspecs.items()):
        #     for k, v in list(spec.items()):
        #         if isinstance(k, bytes):
        #             spec.pop(k)
        #             k = k.decode('utf-8', 'ignore')
        #         if isinstance(v, bytes):
        #             v = v.decode('utf-8', 'ignore')
        #         spec[k] = v
            # print "key:%s spec:%s"%(key,spec)
        
            strmethod = """
class Klass:
    def __init__(self, client, category):
        self._client = client
        self._category = category

    def method(%s):
        '''%s'''
        return self._client.sendcmd(cmd="%s", category=self._category, %s,sendformat="${sendformat}",returnformat="${returnformat}",transporttimeout=transporttimeout)
    """
            strmethod=strmethod.replace("${sendformat}",sendformat)
            strmethod=strmethod.replace("${returnformat}",returnformat)
            args = ["%s=%s" % (x, x) for x in spec['args'][0][1:]]
            params_spec = spec['args'][0]
            if spec['args'][3]:
                params_spec = list(spec['args'][0])
                for cnt, default in enumerate(spec['args'][3][::-1]):
                    cnt += 1
                    params_spec[-cnt] += "=%r" % default
            args.append("_agentid=_agentid")
            params = ', '.join(params_spec)
            params += ",transporttimeout=5"
            params += ",_agentid=0"
            strmethod = strmethod % (params, spec['doc'], key, ", ".join(args), )
            # try:
            ns = dict()
            exec(compile(strmethod, '<string>', 'exec'), ns)
            # except Exception as e:
                # raise j.exceptions.RuntimeError("could not exec the client method, error:%s, code was:%s"%(e,strmethod))
            klass = ns['Klass'](self, category)
            setattr(client, key, klass.method)
                # print strmethod
        return client

    def sendcmd(self, cmd, sendformat=None, returnformat=None, category=None,transporttimeout=5,**args):
        """
        formatstring is right order of formats e.g. mc means messagepack & then compress
        formats see: j.data.serializer.serializers.get(?

        return is the deserialized data object
        """
        if "_agentid" not in args:
            args["_agentid"]=0
        return self.sendMsgOverCMDChannel(cmd, args, sendformat, returnformat, category=category,transporttimeout=transporttimeout)

    def perftest(self):
        start = time.time()
        nr = 10000
        #print(("start perftest for %s for ping cmd" % nr))
        for i in range(nr):
            if not self.sendcmd("ping") == "pong":
                raise j.exceptions.RuntimeError("ping did not return pong.")
        stop = time.time()
        nritems = nr / (stop - start)
        #print(("nr items per sec: %s" % nritems))
        #print(("start perftest for %s for cmd ping" % nr))
        for i in range(nr):
            if not self.sendcmd("pingcmd") == "pong":
                raise j.exceptions.RuntimeError("ping did not return pong.")
        stop = time.time()
        nritems = nr / (stop - start)
        #print(("nr items per sec: %s" % nritems))

class Transport:

    def connect(self, sessionid=None):
        """
        everwrite this method in implementation to init your connection to server (the transport layer)
        """
        raise j.exceptions.RuntimeError("not implemented")

    def close(self):
        """
        close the connection (reset all required)
        """
        raise j.exceptions.RuntimeError("not implemented")

    def sendMsg(self, category, cmd, data, sendformat="j", returnformat="j"):
        """
        overwrite this class in implementation to send & retrieve info from the server (implement the transport layer)

        @return (resultcode,returnformat,result)
                item 0=cmd, item 1=returnformat (str), item 2=args (dict)
        resultcode
            0=ok
            1= not authenticated
            2= method not found
            2+ any other error
        """
        raise j.exceptions.RuntimeError("not implemented")
        # send message, retry if needed, retrieve message

    def __str__(self):
        # return "%s %s:%s" % (self.__class__.__name__, self._addr, self._port)
        return "%s" % (self.__class__.__name__)
