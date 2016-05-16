from JumpScale import j
import requests
from requests.auth import HTTPBasicAuth
import os


class GrafanaFactory(object):
    def __init__(self):
        self.__jslocation__ = "j.clients.grafana"

    def get(self, url="http://localhost:3000", username="admin", password="admin"):
        return GrafanaClient(url, username, password)

    def getByInstance(self, instance=None):
        if instance is None or instance == '':
            service = j.atyourservice.findServices(role="grafana_client", first=True)
        else:
            service = j.atyourservice.findServices(role="grafana_client", instance=instance, first=True)
        hrd = service.hrd

        url = hrd.get("param.url")
        username = hrd.get("param.username")
        password = hrd.get("param.password")
        return self.get(url, username, password)


class GrafanaClient(object):
    def __init__(self, url, username, password):
        self._url = url
        self.setAuth(username, password)

    def ping(self):
        url = os.path.join(self._url, 'api/org/')
        try:
            self._session.get(url).json()
            return True
        except:
            return False

    def setAuth(self, username, password):
        self._username = username
        self._password = password
        auth = HTTPBasicAuth(username, password)
        self._session = requests.session()
        self._session.auth = auth

    def updateDashboard(self, dashboard):
        url = os.path.join(self._url, 'api/dashboards/db')
        data = {'dashboard': dashboard, 'overwrite': True}
        result = self._session.post(url, json=data)
        return result.json()

    def listDashBoards(self):
        url = os.path.join(self._url, 'api/search/')
        return self._session.get(url).json()

    def isAuthenticated(self):
        url = os.path.join(self._url, 'api/org/')
        return self._session.get(url).status_code != 401

    def delete(self, dashboard):
        url = os.path.join(self._url, 'api/dashboards', dashboard['uri'])
        return self._session.delete(url)

    def changePassword(self, newpassword):
        url = os.path.join(self._url, 'api/user/password')
        data = {'newPassword': newpassword, 'oldPassword': self._password}
        result = self._session.put(url, json=data).json()
        self.setAuth(self._username, newpassword)
        return result

    def listDataSources(self):
        url = os.path.join(self._url, 'api/datasources/')
        return self._session.get(url).json()

    def addDataSource(self, data):
        url = os.path.join(self._url, 'api/datasources/')
        return self._session.post(url, json=data).json()
