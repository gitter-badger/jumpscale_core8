from JumpScale import j

# import urllib
# import requests
# from requests.auth import HTTPBasicAuth
# from . import gitlab
import os

from GitlabInstance import *

# INFOCACHE = dict()

class GitlabFactory:
    """
    Gitlab client enables administrators and developers leveraging Gitlab services through JumpScale
    """

    def __init__(self):
        self.__jslocation__ = "j.clients.gitlab"
        self.logger = j.logger.get('j.clients.gitlab')
        self.connections = {}

    def get(self,gitlaburl="",login="",passwd="",instance="main"):
        """
        example for gitlaburl
            https://despiegk:dddd@git.aydo.com
        can also be without login:passwd
            e.g. https://git.aydo.com and specify login/passwd

        if gitlaburl is empty then
            hrd is used as follows:
            hrd=j.application.getAppInstanceHRD("gitlab_client",instance)
            gitlaburl=hrd.get("gitlab.client.url")
            login=hrd.get("gitlab.client.login")
            passwd=hrd.get("gitlab.client.passwd")

        """
        if login =="":
            if not gitlaburl.find("@"):
                raise j.exceptions.Input("login not specified, expect an @ in url")
            data=gitlaburl.split("@")[0]
            if data.find("http")==0:
                data=data.split("//")[1]
            login,passwd=data.split(":")
            gitlaburl=gitlaburl.replace("%s:%s@"%(login,passwd),"")

        return GitlabInstance(addr=gitlaburl,login=login,passwd=passwd,instance=instance)

    def getAccountnameReponameFromUrl(self,url):
        repository_host, repository_type, repository_account, repository_name, repository_url= j.do.rewriteGitRepoUrl( url)
        repository_name=repository_name.replace(".git","")
        return (repository_account, repository_name)
