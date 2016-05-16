from JumpScale import j
import requests


class SkyDNSClientFactory():

    def __init__(self):
        self.__jslocation__ = "j.clients.skydns"

    def get(self, baseurl, username=None, password=None):
        """
        baseurl: str, url of the etcd for skydns e.g: https://dns1.aydo.com/etcd
        """
        return SkyDNSClient(baseurl, username, password)


class SkyDNSClient():

    def __init__(self, baseurl='', username=None, password=None):
        self._session = requests.Session()
        self.baseurl = ('%s/v2/keys/skydns/' % baseurl)
        self.username = username
        self.password = password
        self.authenticate(username, password)

    def authenticate(self, username, password):
        if self.username and self.password:
            base = self.username + ":" + self.password
            auth_header = "Basic " + j.data.serializer.base64.dumps(base)
            self._session.headers = {"Authorization": auth_header}

    def _replyParser(self, r):
        if r.status_code == 401:
            return {"error": "not authorized"}
        
        if r.status_code == 404:
            return {"error": "endpoint not found"}
        
        return r.json()
        
    def read(self, endpoint):
        link = self.mkurl(endpoint)

        r = self._session.get(link)

        return self._replyParser(r)

    def write(self, endpoint, data):
        link = self.mkurl(endpoint)

        payload = {'value': j.data.serializer.json.dumps(data)}
        r = self._session.put(link, data=payload)

        return self._replyParser(r)

    def delete(self, endpoint):
        link = self.mkurl(endpoint)

        r = self._session.delete(link)

        return self._replyParser(r)

    def mkurl(self, endpoint, complement=''):
        return '%s%s' % (self.baseurl, endpoint)

    def _hostKey(self, host):
        items = host.split('.')
        items = list(reversed(items))
        key = "/".join(items)
        return key

    def getConfig(self):
        return self.read('config')

    def setConfig(self, config):
        self.write('config', config)
        return self.getConfig()

    # valid for AAAA and CNAME btw
    def setRecordA(self, name, target, priority=20, ttl=3600):
        key = self._hostKey(name)
        self.write(key, {'host': target, 'priority': priority, 'ttl': ttl})
        return self.read(key)

    def setRecordMX(self, name, target, priority=20, ttl=3600):
        key = self._hostKey(name)
        self.write(key, {'host': target, 'priority': priority, 'ttl': ttl, 'mail': True})
        return self.read(key)
    
    def setRecordTXT(self, name, content, ttl=3600):
        key = self._hostKey(name)
        self.write(key, {'text': content, 'ttl': ttl})
        return self.read(key)
        
    def removeRecordA(self, name):
        key = self._hostKey(name)
        self.delete(key)
        return True

    def exists(self, name):
        key = self._hostKey(name)
        resp = self.read(key)
        if 'node' in resp and 'value' in resp['node']:
            host = None
            value = resp['node']['value']
            if j.data.types.string.check(value):
                value = j.data.serializer.json.loads(value)
                host = value['host']
            elif j.data.types.dict.check(value):
                host = value['host']
            else:
                raise j.exceptions.RuntimeError("Bad response format (%s)", resp)
            return (True, host)
        return (False, None)
