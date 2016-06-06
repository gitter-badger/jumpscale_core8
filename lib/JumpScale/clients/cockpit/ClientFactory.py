from JumpScale import j
from client import Client
import requests


class CockpitFactory:

    def __init__(self):
        self.__jslocation__ = "j.clients.cockpit"
        self._clients = {}

    def get_jwt(self, oauthtoken, scope):
        """
        oauthtoken: str, oauth token
        scope: list, list of scope you want to have access to
        """
        if j.data.types.string.check(scope):
            scope = [scope]
        session = requests.Session()
        session.headers.update({'Authorization': 'token %s' % oauthtoken})
        jwturl = 'https://itsyou.online/v1/oauth/jwt?scope={scope}'.format(scope=','.join(scope))
        response = session.post(jwturl, verify=False)
        response.raise_for_status()
        result = response.text
        return result

    def getClient(self, base_uri, jwt):
        if base_uri not in self._clients:
            self._clients[base_uri] = Client(base_uri, jwt)
        return self._clients[base_uri]
