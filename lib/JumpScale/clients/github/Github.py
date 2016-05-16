from JumpScale import j
from JumpScale.tools.zip.ZipFile import ZipFile

from Repository import GithubRepo
from User import User


try:
    import github
except:
    cmd = "pip3 install pygithub"
    j.do.execute(cmd)
    import github


class GitHubFactory(object):

    def __init__(self):
        self.__jslocation__ = "j.clients.github"
        self._clients={}

    # def getRepoClient(self, account, reponame):
    #     return GitHubRepoClient(account, reponame)

    def getClient(self, secret):
        if secret not in self._clients:
            self._clients[secret]= GitHubClient(secret)
        return self._clients[secret]

class GitHubClient():

    def __init__(self, secret):
        self.api = github.Github(secret)
        self.users = {}
        self.repos = {}        

    def getRepo(self, fullname):
        """
        fullname e.g. incubaid/myrepo
        """
        if fullname not in self.repos:
            r= GithubRepo(self, fullname)
            self.repos[fullname]=r
        return self.repos[fullname]

    def getUserLogin(self, githubObj):
        if githubObj is None:
            return ""
        if githubObj.login not in self.users:
            user = User(self, githubObj=githubObj)
            self.users[githubObj.login] = user
        return self.users[githubObj.login].login

    def getUser(self, login="", githubObj=None):
        if login in self.users:
            return self.users[login]

        if githubObj is not None:
            if githubObj.login not in self.users:
                user = User(self, githubObj=githubObj)
                self.users[githubObj.login] = user
            return self.users[githubObj.login]

