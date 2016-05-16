from JumpScale import j

import urllib.request, urllib.parse, urllib.error


class OpenvcloudFactory(object):
    def __init__(self):
        self.__jslocation__ = "j.tools.openvcloud"

    def get(self, apiurl='www.mothership1.com', branch='master'):
        return Openvcloud(apiurl, branch)


class Openvcloud(object):
    def __init__(self, apiurl, branch='master'):
        self._spacesecret = None
        self.apiURL = apiurl
        self.api = j.clients.ms1.get(apiurl, 443)
        self.db = j.servers.kvs.getFSStore("aysgit")
        self.reset = False
        self.branch = branch

    def connect(self, login, passwd, location,cloudspace,reset=False):
        """
        example locations on mothership1:  ca1 (canada),us2 (us), eu2 (belgium), eu1 (uk)
        @param reset if True then will not look at history
        """
        self.reset=reset
        self.login=login
        self.passwd=passwd
        self.location=location
        self.cloudspace=cloudspace
        self._spacesecret = self.api.getCloudspaceSecret(login, passwd, cloudspace, location)
        return self._spacesecret

    def actionCheck(self,gitlaburl,actionname):
        if self.reset:
            return False

        key="%s__%s" % (gitlaburl, actionname)

        if self.db.exists("", key):
            print("Action: %s done" % actionname)
            return self.db.get("", key)

        return False

    def actionDone(self,gitlaburl,actionname,args=None):
        key = "%s__%s" % (gitlaburl,actionname)
        self.db.set("", key, args)

    def initAYSGitVM(self, gitlaburl, gitlablogin, gitlabpasswd, recoverypasswd, delete=False):
        """

        gitlaburl example
        https://git.aydo.com/openvcloudEnvironments/testkds.git
        #do not use login:passwd@ in the url

        master git machine is the machine which holds all the configuration for the master environment of an openvcloud

        example:
        cl.initMasterGitVMovc("despiegk","????","eu2","BE","git.aydo.com",\
            gitlablogin="despiegk",gitlabpasswd="????",\
            gitlabAccountname="test",gitlabReponame="testspace",recoverypasswd="9999")

        will do the following
        - init connection with openvcloud API
        - create machine which will host the git repo for this openvcloud env
        - do portforward from internet to git master for ssh (port 22)
        - create remote ssh key pair
        - secure the gitvm (give local user sshpair access)
        - install jumpscale
        - create the required repo on gitlab
        - push initial content
        - pull git repo onto the vmachine
        - create openvcloud connection ays on vmachine so that future connections to openvcloud can be made

        """

        #check gitlab repo exists or needs to be created
        # create new git repo
        print("[+] creating git repository")

        if gitlaburl.find("@")!=-1:
            raise j.exceptions.Input('[-] do not use "login:passwd@" in the url')

        if not gitlaburl.startswith("http"):
            gitlaburl = "https://%s" % gitlaburl

        gitlabAccountname, gitlabReponame = j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)
        gitlaburl0 = "/".join(gitlaburl.split("/")[:3])

        print('[+] git group: %s' % gitlabAccountname)
        print('[+] environment: %s' % gitlabReponame)
        print('[+] git branch: %s' % self.branch)

        gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)
        if self.actionCheck(gitlaburl, "gitcreate") is False:
            gitlab.createProject(gitlabAccountname, gitlabReponame, public=False)
            self.actionDone(gitlaburl, "gitcreate")

        print("[+] get secret key for cloud api")

        if self._spacesecret is None:
            raise j.exceptions.Input('[-] no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        print("[+] checking local ssh key")

        keypath = '/root/.ssh/id_rsa'
        if not j.sal.fs.exists(path=keypath):
            print("[+] generating local rsa key")
            j.sal.ubuntu.sshkeys_generate()

        if len(recoverypasswd) < 6:
            raise j.exceptions.Input("[-] recovery passwd needs to be at least 6 chars")

        if self.actionCheck(gitlaburl, "machinecreate") is False:
            # create ovc_git vm
            id, ip, port = self.api.createMachine(spacesecret, 'ovc_git', memsize='0.5', ssdsize='10', imagename='ubuntu.14.04.x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)


            # portforward 22 to 22 on ovc_git
            self.api.createTcpPortForwardRule(spacesecret, 'ovc_git', 22, pubipport=22)

            # ssh connetion to the vm
            cl = j.ssh.connect(ip, port, keypath=keypath, verbose=True)
            cl.fabric.api.env['forward_agent'] = True

            # generate key pair on the vm
            print('[+] generating keypair on the vm')
            cl.ssh.keygen('root', 'rsa')

            # secure vm and give access to the local machine
            u = j.ssh.unix.get(cl)
            u.secureSSH('', recoverypasswd=recoverypasswd)
            self.actionDone(gitlaburl, "machinecreate", (ip, port))
        else:
            ip, port = self.actionCheck(gitlaburl, "machinecreate")
            cl = j.ssh.connect(ip, 22, keypath=keypath, verbose=True)
            cl.fabric.api.env['forward_agent'] = True

        if self.actionCheck(gitlaburl, "jumpscale") is False:
            # install Jumpscale
            print("[+] installing jumpscale")
            
            with cl.fabric.api.shell_env(JSBRANCH=self.branch, AYSBRANCH=self.branch):
                cl.run('echo "[+] setup branch: $JSBRANCH, $AYSBRANCH"')
                cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')

            # print "jumpscale installed"

            print("[+] adding openvcloud domain to atyourservice")
            content = """
metadata.openvcloud            =
    url:'https://git.aydo.com/0-complexity/openvcloud_ays',
"""
            cl.file_append('%s/hrd/system/atyourservice.hrd'%j.dirs.base, content)
            self.actionDone(gitlaburl, "jumpscale")

        if self.actionCheck(gitlaburl, "gitcredentials") is False:
            cl.run('jsconfig hrdset -n whoami.git.login -v "%s"' % gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v "%s"' % urllib.parse.quote_plus(gitlabpasswd))
            infos = gitlab.getUserInfo(gitlablogin)

            email = infos['email'] if 'email' in infos else 'nobody@aydo.com'
            name = infos['name'] if infos['name'] != '' else gitlablogin

            cl.run('git config --global user.email "%s"' % email)
            cl.run('git config --global user.name "%s"' % name)
            self.actionDone(gitlaburl, "gitcredentials")

        repopath = "/opt/code/git/%s/%s/" % (gitlabAccountname, gitlabReponame)

        if self.actionCheck(gitlaburl, "gitlabclone") is False:
            # clone templates repo and change url
            _, _, _, _, repoURL = j.do.rewriteGitRepoUrl(gitlaburl, gitlablogin, urllib.parse.quote_plus(gitlabpasswd))

            if not cl.file_exists(repopath):
                host = 'https://%s:%s@%s' % (gitlablogin, urllib.parse.quote_plus(gitlabpasswd), 'git.aydo.com')
                cl.run('git clone %s/openvcloudEnvironments/OVC_GIT_Tmpl.git %s' % (host, repopath))
                cl.run('cd %s; git remote set-url origin %s' % (repopath, repoURL))

                # Note: rebase prevents for asking to merge local tree with remote
                cl.run('ssh-add -L')
                cl.run('cd %s; git pull --rebase' % repopath)

            self.actionDone(gitlaburl, "gitlabclone")
        
        if self.actionCheck(gitlaburl, 'copyKeys') is False:
            keys = {
                '/root/.ssh/id_rsa': j.sal.fs.joinPaths(repopath, 'keys', 'git_root'),
                '/root/.ssh/id_rsa.pub': j.sal.fs.joinPaths(repopath, 'keys', 'git_root.pub'),
            }

            for source, dest in keys.items():
                content = cl.file_read(source)
                cl.file_write(dest, content)

            self.actionDone(gitlaburl, 'copyKeys')

        if self.actionCheck(gitlaburl, "ms1client") is False:
            # create ms1_client to save ms1 connection info
            args = 'instance.param.location:%s instance.param.login:%s instance.param.passwd:%s instance.param.cloudspace:%s' % (self.location, self.login, self.passwd, self.cloudspace)
            cl.run('cd %s; ays install -n ms1_client --data "%s"' % (repopath, args))
            self.actionDone(gitlaburl, "ms1client")

        if self.actionCheck(gitlaburl, "gitlab_client") is False:
            # create gitlab_client to save gitlab connection info
            scheme, host, _, _, _ = j.do.rewriteGitRepoUrl(gitlaburl)
            url = scheme+host
            args = 'instance.gitlab.client.url:%s instance.gitlab.client.login:%s instance.gitlab.client.passwd:%s' % (url, gitlablogin, gitlabpasswd)
            cl.run('cd %s; ays install -n gitlab_client --data "%s"' % (repopath, args))
            self.actionDone(gitlaburl, "gitlab_client")
        
        if self.actionCheck(gitlaburl, "ovc_setup") is False:
            vmachine = self.api.getMachineObject(self._spacesecret, 'ovc_git')
            vspace = self.api.getCloudspaceObj(self._spacesecret)
        
            # create ovc_setup instance to save settings
            args  = 'instance.ovc.environment:%s ' % gitlabReponame
            args += 'instance.ovc.path:/opt/code/git/%s/%s ' % (gitlabAccountname, gitlabReponame)
            args += 'instance.ovc.ms1.instance:main '
            args += 'instance.ovc.gitlab_client.instance:main ' 
            args += 'instance.ovc.password:rooter '
            args += 'instance.ovc.bootstrap.port:5000 '
            args += 'instance.ovc.bootstrap.host:%s ' % vmachine['interfaces'][0]['ipAddress']
            args += 'instance.ovc.cloudip:%s ' % vspace['publicipaddress']
            args += 'instance.ovc.gitip:%s ' % vmachine['interfaces'][0]['ipAddress']
            
            cl.run('cd %s; ays install -n ovc_setup --data "%s"' % (repopath, args))
            self.actionDone(gitlaburl, "ovc_setup")


        if self.actionCheck(gitlaburl, "rememberssh") is False:
            # create ms1_client to save ms1 connection info
            args = 'instance.param.recovery.passwd:%s instance.param.ip:%s' % (recoverypasswd, ip)
            cl.run('cd %s; ays install -n git_vm --data "%s"' % (repopath, args))
            cl.run('git config --global push.default simple')
            cl.run('cd %s;jscode push' % repopath)
            self.actionDone(gitlaburl, "rememberssh")

        print("[+] setup completed")

    def connectAYSGitVM(self, gitlaburl, gitlablogin, gitlabpasswd, setup=False):
        """
        @param gitlaburl= 'https://git.aydo.com/openvcloudEnvironments/scaleout1'
        @param setup: if True, will launch the script to resume setup of the openvcloud
                      if False, you will just have a prompt

        """
        keypath='/root/.ssh/id_rsa'
        if self.actionCheck(gitlaburl, "machinecreate"):
            # means on this machien we have alrady created the machine so we have the credentials
            ip, port = self.actionCheck(gitlaburl, "machinecreate")
            cl = j.ssh.connect(ip, 22, keypath=keypath, verbose=True)
        else:
            cl = j.clients.gitlab.get("https://git.aydo.com", gitlablogin, gitlabpasswd)
            hrd = cl.getHRD("openvcloudEnvironments", "scaleout1", "services/openvcloud__git_vm__main/service.hrd")

        if self.actionCheck(gitlaburl, "gitcredentials"):
            gitlaburl0 = "/".join(gitlaburl.split("/")[:3])
            gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)
            infos = gitlab.getUserInfo(gitlablogin)

            cl.run('jsconfig hrdset -n whoami.git.login -v "%s"' % gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v "%s"' % urllib.parse.quote_plus(gitlabpasswd))

            cl.run('git config --global user.email "%s"' % infos['email'])
            cl.run('git config --global user.name "%s"' % infos['name'] if infos['name'] != '' else gitlablogin)

        cl.run('ays mdupdate')
        
        if setup:
            gitlaburl0 = "/".join(gitlaburl.split("/")[:3])
            temp = gitlaburl.split("/")
            repopath = '/opt/code/git/%s/%s' % (temp[3], temp[4])
            
            print('[+] resuming setup')
            # FIXME
            cl.run('cd %s; wget http://arya.maxux.net/temp/gig/aio.py -O aio.py' % repopath)
            # cl.run('cd %s; jspython setup.py' % (repopath, args))

        cl.fabric.api.open_shell()

    def initVnasCloudSpace(self, gitlaburl, gitlablogin, gitlabpasswd, jsBranch='master', delete=False):
        print("[+] creating git repository")

        if gitlaburl.find("@")!=-1:
            raise j.exceptions.Input('[-] do not use "login:passwd@" in the url')

        if not gitlaburl.startswith("http"):
            gitlaburl = "https://%s" % gitlaburl

        gitlabAccountname, gitlabReponame = j.clients.gitlab.getAccountnameReponameFromUrl(gitlaburl)
        gitlaburl0 = "/".join(gitlaburl.split("/")[:3])

        print('[+] git group: %s' % gitlabAccountname)
        print('[+] environment: %s' % gitlabReponame)

        gitlab = j.clients.gitlab.get(gitlaburl0, gitlablogin, gitlabpasswd)
        if self.actionCheck(gitlaburl, "gitcreate") is False:
            gitlab.createProject(gitlabAccountname, gitlabReponame, public=False)
            self.actionDone(gitlaburl, "gitcreate")

        print("get secret key for cloud api")
        if self._spacesecret is None:
            raise j.exceptions.Input('no spacesecret set, need to call connect() method first')
        else:
            spacesecret = self._spacesecret

        print("check local ssh key exists")
        keypath='/root/.ssh/id_rsa'
        if not j.sal.fs.exists(path=keypath):
            print("generate local rsa key")
            j.sal.ubuntu.sshkeys_generate()

        if self.actionCheck(spacesecret, "vnas_machinecreate") is False:
            # create ovc_git vm
            id, ip, port = self.api.createMachine(spacesecret, 'vnas_master', memsize='2', ssdsize='10', imagename='ubuntu 14.04 x64',sshkey='/root/.ssh/id_rsa.pub',delete=delete)

            # portforward 22 to 22 on ovc_git
            self.api.createTcpPortForwardRule(spacesecret, 'vnas_master', 22, pubipport=1500)

            # ssh connetion to the vm
            cl = j.ssh.connect(ip, port, keypath=keypath, verbose=True)
            cl.fabric.api.env['forward_agent'] = True

            # generate key pair on the vm
            print('generate keypair on the vm')
            cl.ssh.keygen('root', 'rsa')

            self.actionDone(spacesecret, "vnas_machinecreate", (ip, port))
        else:
            ip, port = self.actionCheck(spacesecret, "vnas_machinecreate")
            cl = j.ssh.connect(ip, port, keypath=keypath, verbose=True)
            cl.fabric.api.env['forward_agent'] = True

        if self.actionCheck(spacesecret, "vnas_jumpscale") is False:
            # install Jumpscale
            print("install jumpscale")
            with cl.fabric.api.shell_env(JSBRANCH=jsBranch, AYSBRANCH=jsBranch):
                cl.run('curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/master/install/install.sh > /tmp/js7.sh && bash /tmp/js7.sh')
            print("jumpscale installed")

            print("add openvcloud domain to atyourservice")
            content = """
metadata.openvcloud            =
    url:'https://git.aydo.com/0-complexity/openvcloud_ays',
"""
            cl.file_append('%s/hrd/system/atyourservice.hrd'%j.dirs.base, content)
            self.actionDone(spacesecret, "vnas_jumpscale")

        if self.actionCheck(gitlaburl, "vnas-gitlabclone") is False:
            # clone templates repo and change url
            _, _, _, _, repoURL = j.do.rewriteGitRepoUrl(gitlaburl, gitlablogin, urllib.parse.quote_plus(gitlabpasswd))

            repopath = "/opt/code/git/%s/%s/" % (gitlabAccountname, gitlabReponame)

            if not cl.file_exists(repopath):
                cl.run('git clone %s %s' % (gitlaburl, repopath))

            self.actionDone(gitlaburl, "gitlabclone")

        if self.actionCheck(spacesecret, "vnas-gitcredentials") is False:
            cl.run('jsconfig hrdset -n whoami.git.login -v "%s"' % gitlablogin)
            cl.run('jsconfig hrdset -n whoami.git.passwd -v "%s"' % urllib.parse.quote_plus(gitlabpasswd))
            self.actionDone(spacesecret, "vnas-gitcredentials")

        if self.actionCheck(gitlaburl, "vnas-gitlabclone") is False:
            # clone templates repo and change url
            _, _, _, _, repoURL = j.do.rewriteGitRepoUrl(gitlaburl, gitlablogin, urllib.parse.quote_plus(gitlabpasswd))

            repopath = "/opt/code/git/%s/%s/" % (gitlabAccountname, gitlabReponame)

            if not cl.file_exists(repopath):
                cl.run('git clone %s %s' % (gitlaburl, repopath))

            self.actionDone(gitlaburl, "gitlabclone")

        if self.actionCheck(spacesecret, "vnas_ovc_client") is False:
            # create ovc_client to save ovc connection info
            args = 'instance.param.location:%s instance.param.login:%s instance.param.passwd:%s instance.param.cloudspace:%s instance.param.apiurl:%s' % (self.location, self.login, self.passwd, self.cloudspace, self.apiURL)
            cl.run('cd %s; ays install -n ovc_client --data "%s"' % (repopath, args))
            self.actionDone(spacesecret, "vnas_ovc_client")

        ss = cl.host().split(':')
        ip, port = ss[0], ss[1]
        print("connect to the vnas_master with\nssh root@%s -p %s" % (ip, port))
        print("then do 'cd %s; ays install -n vnas_aio'" % repopath)

    def vmExists(self, spacesecret, name):
        try:
            cl.api.getMachineObject(cl._spacesecret, 'vnas_master')
        except Exception as e:
            if e.message and e.message.find('Could not find machine') != -1:
                return False
        return True
