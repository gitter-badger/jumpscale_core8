import base64


from JumpScale import j

# import gitlab3
try:
    import gitlab
except Exception as e:
    cmd="pip install pyapi-gitlab"
    if str(e).find("No module named 'gitlab'")!=-1:
        j.sal.process.executeWithoutPipe(cmd)
    import gitlab


class GitlabInstance():
    """
    Wrapper around gitlab3 library with Caching capabilities to improve performance.
    """

    # GITLAB permissions as keys mapped to jumpscale permissions scheme
    PERMISSIONS = {
        10:'',    #guest
        20:'r',   #reporter
        30:'rw',  #developer
        40:'rwa', #master
        50:'rwa'  #owner
    }

    def __init__(self,addr="",login="",passwd="",instance="main"):

        if addr=="":
            hrd=j.application.getAppInstanceHRD("gitlab_client",instance)
            self.addr=hrd.get("gitlab.client.url")
            self.login=hrd.get("gitlab.client.login")
            self.passwd=hrd.get("gitlab.client.passwd")
        else:
            self.addr=addr
            self.login=login
            self.passwd=passwd

        self.gitlab = gitlab.Gitlab(addr)
        self.gitlab.login(self.login,self.passwd)
        self.isLoggedIn = True

        # # self.gitlab=gitlab3.GitLab(self.addr)
        # self.isLoggedIn = False

        #will be default 5 min
        self.cache=j.db.cache.get(j.servers.kvs.getRedisStore(namespace="cache"))

    def getFile(self,group,project,path):
        """
        project = name of project in group
        """
        project=self.getProject(project)
        project["id"]

        res=self.gitlab.getfile(project["id"],path,"master")
        if res==False:
            raise j.exceptions.Input("cannot find file:%s in gitlab in project:%s"%(path,project))

        return base64.decodestring(res["content"])

    def getHRD(self,group,project,path):
        content=self.getFile(group,project,path)
        return j.data.hrd.get(content=content)

    def downloadFile(self,group,project,path,dest):
        content=self.getFile(group,project,path)
        j.sal.fs.createDir(j.sal.fs.getDirName(dest))
        j.sal.fs.writeFile(filename=dest,contents=content)

    def _getFromCache(self,key,renew=False):
        if renew:
            self.cache.delete(key)
        expired,result = self.cache.get(key)
        return result


    def getGroupInfo(self, groupname, renew=False):
        """
        Get a group info

        @param groupname: groupname
        @type groupname: ``str``
        @param renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type renew: ``boolean``
        @param die: Raise exception if group not found
        @type die: ``boolean``
        @return: ``` gitlab3.Group ```

        """
        groups=self.getGroups(renew=renew)
        groupname=groupname.lower()
        items=[item for item in groups if item["name"].lower()==groupname]
        if len(items)>0:
            return items[0]
        else:
            raise j.exceptions.Input("cannot find group:%s in gitlab"%groupname)


        # result=self._getFromCache(groupname)
        # if result!=None:
        #     return result
        # else:
        #     from IPython import embed
        #     print "DEBUG NOW groupinfo"
        #     embed()

        #     group = self.gitlab.find_group(name=groupname)
        #     self.cache.set(groupname,group)

        # if die:
        #     raise j.exceptions.Input("Cannot find group with name:%s"%groupname)
        # else:
        #     return None

    def getProject(self, name, renew=False):
        """
        @param name: Project/Project name
        @param renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st

        """
        projects=self.getProjects()
        name=name.lower()
        items=[item for item in projects if item["name"].lower()==name]
        if len(items)>0:
            return items[0]
        else:
            logger = j.logger.get('GitlabInstance')
            logger.warn_tb(j.exceptions.Input, "cannot find group:%s in gitlab"%name)
            return False

    def getProjects(self):
        key="projects"
        result=self._getFromCache(key,renew=False)
        if result==None:
            result = self.gitlab.getprojects()
            self.cache.set(key,result)
        return result


    def createProject(self,group, name, public=False):
        """
        Create a project in a certain group

        @param group: groupname
        @type group: ``str``
        @param name: space name
        @type name: ``str``
        """
        group2=self.getGroupInfo(group, renew=True)

        ttype=self.addr.split("/",1)[1].strip("/ ")
        if ttype.find(".")!=-1:
            ttype=ttype.split(".",1)[0]
        path="%s/%s/%s/%s"%(j.dirs.codeDir,ttype,group,name)
        if not self.getProject(name, renew=True):
            self.gitlab.createproject(name,public=public,namespace_id=group2['id'])
            proj=self.getProject(name, renew=True)
            j.sal.fs.remove(path, force=True)
            j.sal.fs.createDir(path)
            def do(cmd):
                j.sal.process.executeWithoutPipe("cd %s;%s"%(path,cmd))
            do("git init")
            do("touch README")
            do("git add README")
            do("git commit -m 'first commit'")
            addr=self.addr.split("/",1)[1].strip("/ ")
            self.passwd = self.passwd.replace('$','\$')
            do("git remote add origin https://%s:%s@%s/%s/%s.git"%(self.login,self.passwd,addr,group,name))
            do("git push -u origin master")
        else:
            proj=self.getProject(name, renew=True)
            url=proj['web_url']
            if group:
                return group
            j.do.pullGitRepo(url=url, dest=None, login=self.login, passwd=self.passwd, depth=1, ignorelocalchanges=False, reset=False, branch=None, revision=None)

        return proj,path

    def getUserInfo(self, username, renew=False):
        """
        Returns user info

        @param username: username
        @type username: ``str``
        @return: ```gitlab3.User```
        """
        users = self.gitlab.getusers(search=username)
        user = [u for u in users if u['username'] == username]
        if len(user) == 1:
            return user[0]
        else:
            raise j.exceptions.OPERATIONS('username %s not found' % username)

    def userExists(self, username, renew=False):
        """
        Check user exists

        @param username: username
        @type username: ``str``No JSON object could be decoded
        @return: ``bool``
        """
        return bool(self.getUserInfo(username, renew))

    def createUser(self, username, password, email, groups):
        id = self.gitlab.add_user(username=username, password=password, email=email)
        for group in groups:
            g = self.gitlabclient.find_group(name=group)
            g.add_member(id)
            g.save()
        self.listUsers(renew=True)

    def listUsers(self, renew=False):
        """
        Get All users
        @param renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type renew: ``boolean``
        @return: ``lis``
        """
        if not renew:
            result = self._getFromCache(self.login, 'users')
            if not result['expired']:
                return result['data']
        users =  self.gitlab.users()
        self._addToCache(self.login, 'users', users)
        return self._getFromCache(self.login, 'users')['data']

    def getGroups(self, renew=False):
        """
        GET ALL groups in gitlab that user has access to

        @param renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
        @type renew: ``boolean``
        @return: ``lis``
        """
        key="groups"
        result=self._getFromCache(key,renew=renew)
        if result==None:
            result = self.gitlab.getgroups()
            self.cache.set(key,result)
        return result



    #     if not renew:
    #         result =  self._getFromCache(self.login, 'groups')
    #         if not result['expired']:
    #             return result['data']
    #     all_groups = self.gitlab.groups()
    #     self._addToCache(self.login, 'groups', all_groups)
    #     return self._getFromCache(self.login, 'groups')['data']

    # # def getGroups(self,username, renew=False):
    #     """
    #     Get groups for a certain user

    #     @param username: username
    #     @type username: ``str``
    #     @param renew: If True, get data from gitlab backend then update cache, otherwise try cache 1st
    #     @type renew: ``boolean``
    #     @return: ``lis``
    #     """

    #     if not renew:
    #         result = self._getFromCache(username, 'groups')
    #         if not result['expired']:
    #             return result['data']
    #     try:
    #         groups =  [ group.name for group in self.gitlab.groups(sudo=username) ]
    #         self._addToCache(username, 'groups', groups)
    #     except gitlab3.exceptions.ForbiddenRequest:
    #         self._addToCache(username, 'groups', [])
    #     return self._getFromCache(username, 'groups')['data']

    def getUserProjectRights(self, username, space, **kwargs):
        """

        10:'', #guest
        20:'r', #reporter
        30:'rw', #developer
        40:'*', #master
        50:'*'  #owner

        @param space: user space (Project) in gitlab
        @type space: ```gitlab3.Project```
        """
        prefix = "%s_" % username
        if  prefix in space:
            space = space.replace(prefix, '')

        space = self.getProject(space)
        if not space:
            raise j.exceptions.RuntimeError("Project %s not found" % space)

        rights = space.find_member(username=username)
        if rights:
            return username, self.PERMISSIONS[rights.access_level]
        return username, ''

    def getUserProjectsObjects(self, username, renew=False):
        """
        Get userspace objects (not just names) for a specific user
        Gitlab userspaces always start with 'portal_'

        @param username: username
        @type username: `str`
        @param bypass_cache: If True, Force getting data from gitlab backend, otherwise try to get it from cache 1st
        @type bypass_cache:`bool`
        """
        if not renew:
            result =  self._getFromCache(username, 'spaces')
            if not result['expired']:
                return result['data']

        try:
            userspaces =  [p for p in self.gitlab.find_projects_by_name('portal_', sudo=username)]
            self._addToCache(username, 'spaces', userspaces)
        except gitlab3.exceptions.ForbiddenRequest:
            self._addToCache(username, 'spaces', [])
        return self._getFromCache(username, 'spaces')['data']

    def getUserProjects(self, username, renew=False):
        """
        Get userspace names for a specific user
        Gitlab userspaces always start with 'portal_'

        @param username: username
        @type username: `str`
        @param bypass_cache: If True, Force getting data from gitlab backend, otherwise try to get it from cache 1st
        @type bypass_cache:`bool`
        """
        return [p['name'] for p in self.getUserProjectsObjects(username, renew)]