from JumpScale import j
import time
from ActionDecorator import ActionDecorator


class actionrun(ActionDecorator):
    def __init__(self, *args, **kwargs):
        ActionDecorator.__init__(self, *args, **kwargs)
        self.selfobjCode = "cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.apps.portal"


class CuisinePortal:

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine
        self.portal_dir = self.cuisine.core.args_replace('$appDir/portals/')
        self.main_portal_dir = j.sal.fs.joinPaths(self.portal_dir, 'main')

    def install(self, start=True, mongodbip="127.0.0.1", mongoport=27017, influxip="127.0.0.1", influxport=8086, grafanaip="127.0.0.1", grafanaport=3000, login="", passwd=""):
        """
        grafanaip and port should be the external ip of the machine
        Portal install will only install the portal and libs. No spaces but the system ones will be add by default.
        To add spaces and actors, please use addSpace and addActor
        """
        self.cuisine.bash.environSet("LC_ALL", "C.UTF-8")
        if not self.cuisine.core.isMac:
            if not self.cuisine.installer.jumpscale_installed():
                self.cuisine.installerdevelop.jumpscale8()
            self.cuisine.pip.upgrade("pip")
        self.installDeps()
        self.getcode()
        self.linkCode()
        self.serviceconnect(mongodbip=mongodbip, mongoport=mongoport, influxip=influxip,
                            influxport=influxport, grafanaip=grafanaip, grafanaport=grafanaport)
        if start:
            self.start()

    @actionrun(action=True)
    def installDeps(self):
        """
        make sure new env arguments are understood on platform
        """
        deps = """
        cffi==1.5.2
        setuptools
        aioredis
        # argh
        bcrypt
        Beaker
        blinker
        blosc
        # Cerberus
        # certifi
        # cffi
        # click
        # credis
        # crontab
        # Cython
        decorator
        # docker-py
        # dominate
        # ecdsa
        eve
        eve_docs
        eve-mongoengine
        # Events
        # Flask
        # Flask-Bootstrap
        # Flask-PyMongo
        # gitdb
        gitlab3
        # GitPython
        greenlet
        # hiredis
        html2text
        # influxdb
        # ipdb
        # ipython
        # ipython-genutils
        itsdangerous
        Jinja2
        # marisa-trie
        MarkupSafe
        mimeparse
        mongoengine==0.10.6
        msgpack-python
        netaddr
        # paramiko
        # path.py
        pathtools
        # pexpect
        # pickleshare
        psutil
        # psycopg2
        # ptyprocess
        # pycparser
        # pycrypto
        # pycurl
        # pygo
        # pygobject
        pylzma
        pymongo==3.2.1
        pystache
        # python-apt
        python-dateutil
        pytoml
        pytz
        PyYAML
        # pyzmq
        # redis
        # reparted
        requests
        simplegeneric
        simplejson
        six
        # smmap
        # SQLAlchemy
        traitlets
        ujson
        # unattended-upgrades
        urllib3
        visitor
        watchdog
        websocket
        websocket-client
        Werkzeug
        wheel
        # zmq
        """
        self.cuisine.pip.multiInstall(deps)
        self.changeEve()

    @actionrun(action=True)
    def getcode(self):
        self.cuisine.git.pullRepo("https://github.com/Jumpscale/jumpscale_portal8.git")

    @actionrun(action=True)
    def linkCode(self):
        self.cuisine.bash.environSet("LC_ALL", "C.UTF-8")
        destjslib = self.cuisine.core.run("js 'print(j.do.getPythonLibSystem(jumpscale=True))'", showout=False)

        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/lib/portal" % self.cuisine.core.dir_paths[
                                    "codeDir"], "%s/portal" % destjslib, symbolic=True, mode=None, owner=None, group=None)
        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/lib/portal" %
                                    self.cuisine.core.dir_paths["codeDir"], "%s/portal" % self.cuisine.core.dir_paths['jsLibDir'])

        self.cuisine.core.run("js 'j.application.reload()'", showout=False, die=False)

        if not self.portal_dir.endswith("/"):
            self.portal_dir += '/'
        self.cuisine.core.dir_ensure(self.portal_dir)
        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/jslib" %
                                    self.cuisine.core.dir_paths["codeDir"], '%s/jslib' % self.portal_dir)
        self.cuisine.core.dir_ensure(j.sal.fs.joinPaths(self.portal_dir, 'portalbase'))
        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/apps/portalbase/system" %
                                    self.cuisine.core.dir_paths["codeDir"], '%s/portalbase/system' % self.portal_dir)
        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/apps/portalbase/wiki" %
                                    self.cuisine.core.dir_paths["codeDir"], '%s/portalbase/wiki' % self.portal_dir)
        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/apps/portalbase/macros" %
                                    self.cuisine.core.dir_paths["codeDir"], '%s/portalbase/macros' % self.portal_dir)
        self.cuisine.core.file_link("%s/github/jumpscale/jumpscale_portal8/apps/portalbase/templates" %
                                    self.cuisine.core.dir_paths["codeDir"], '%s/portalbase/templates' % self.portal_dir)

        self.cuisine.core.dir_ensure(self.main_portal_dir)

        self.cuisine.core.dir_ensure('%s/base/home/.space' % self.main_portal_dir)
        self.cuisine.core.file_ensure('%s/base/home/home.md' % self.main_portal_dir)

        self.cuisine.core.dir_ensure('$tmplsDir/cfg/portal')
        self.cuisine.core.file_copy(j.sal.fs.joinPaths(self.cuisine.core.dir_paths["codeDir"], 'github/jumpscale/jumpscale_portal8/apps/portalbase/config.hrd'), '$tmplsDir/cfg/portal/config.hrd')

        self.cuisine.core.file_copy(j.sal.fs.joinPaths(self.cuisine.core.dir_paths["codeDir"], 'github/jumpscale/jumpscale_portal8/apps/portalbase/portal_start.py'), self.main_portal_dir)
        content = self.cuisine.core.file_read(j.sal.fs.joinPaths(self.cuisine.core.dir_paths["codeDir"], 'github/jumpscale/jumpscale_portal8/apps/portalbase/config.hrd'))
        configHRD = j.data.hrd.get(content=content, prefixWithName=False)
        configHRD.set('param.cfg.appdir', j.sal.fs.joinPaths(self.portal_dir, 'portalbase'))
        self.cuisine.core.file_write(j.sal.fs.joinPaths(self.main_portal_dir, 'config.hrd'), content=str(configHRD))
        self.cuisine.core.file_copy("%s/jslib/old/images" % self.portal_dir, "%s/jslib/old/elfinder" % self.portal_dir, recursive=True)

    def addSpace(self, spacepath):
        spacename = j.sal.fs.getBaseName(spacepath)
        dest_dir = j.sal.fs.joinPaths(self.cuisine.core.dir_paths['varDir'], 'cfg', 'portals', 'main', 'base', spacename)
        self.cuisine.core.file_link(spacepath, dest_dir)

    def addActor(self, actorpath):
        actorname = j.sal.fs.getBaseName(actorpath)
        dest_dir = j.sal.fs.joinPaths(self.cuisine.core.dir_paths['varDir'], 'cfg', 'portals', 'main', 'base', actorname)
        self.cuisine.core.file_link(actorpath, dest_dir)

    @actionrun(action=True)
    def serviceconnect(self, mongodbip="127.0.0.1", mongoport=27017, influxip="127.0.0.1", influxport=8086, grafanaip="127.0.0.1", grafanaport=3000):
        dest = j.sal.fs.joinPaths(self.cuisine.core.dir_paths['varDir'], 'cfg', "portals")
        dest_cfg = j.sal.fs.joinPaths(dest, 'main', 'config.hrd')
        self.cuisine.core.dir_ensure(dest)
        content = self.cuisine.core.file_read('$tmplsDir/cfg/portal/config.hrd')
        tmp = j.sal.fs.getTempFileName()
        hrd = j.data.hrd.get(content=content, path=tmp)
        hrd.set('param.mongoengine.connection', {'host': mongodbip, 'port': mongoport})
        hrd.set('param.cfg.influx', {'host': influxip, 'port': influxport})
        hrd.set('param.cfg.grafana', {'host': grafanaip, 'port': grafanaport})
        hrd.save()
        self.cuisine.core.file_write(dest_cfg, str(hrd))
        j.sal.fs.remove(tmp)

    @actionrun(action=True)
    def changeEve(self):
        path = self.cuisine.core.run("js 'print(j)'")  # hack, make sure jumpscale has loaded lib before trying to print something
        path = self.cuisine.core.run("js 'print(j.do.getPythonLibSystem(jumpscale=False))'")
        path = j.sal.fs.joinPaths(path, "eve_docs", "config.py")
        if not self.cuisine.core.file_exists(path):
            raise j.exceptions.RuntimeError("Cannot find:%s, to convert to python 3" % path)
        self.cuisine.core.run("2to3-3.5 -f all -w %s" % path)

    @actionrun(action=True, force=True)
    def start(self, passwd=None):
        """
        Start the portal
        passwd : if not None, change the admin password to passwd after start
        """

        dest_dir = j.sal.fs.joinPaths(self.cuisine.core.dir_paths['varDir'], 'cfg')
        cfg_path = j.sal.fs.joinPaths(dest_dir, 'portals/main/config.hrd')
        app_dir = j.sal.fs.joinPaths(dest_dir, 'portals/portalbase')

        self.cuisine.core.file_copy(self.portal_dir, dest_dir, recursive=True, overwrite=True)

        content = self.cuisine.core.file_read(cfg_path)
        hrd = j.data.hrd.get(content=content, prefixWithName=False)
        hrd.set('param.cfg.appdir', app_dir)
        self.cuisine.core.file_write(cfg_path, str(hrd))

        cmd = "jspython portal_start.py"
        self.cuisine.processmanager.ensure('portal', cmd=cmd, path=j.sal.fs.joinPaths(dest_dir, 'portals/main'))

        if passwd is not None:
            self.set_admin_password(passwd)

    @actionrun(action=True, force=True)
    def stop(self):
        self.cuisine.processmanager.stop('portal')

    def set_admin_password(self, passwd):
        # wait for the admin user to be created by portal
        timeout = 60
        start = time.time()
        resp = self.cuisine.core.run('jsuser list', showout=False, force=True)
        while resp.find('admin') == -1 and start + timeout > time.time():
            try:
                time.sleep(2)
                resp = self.cuisine.core.run('jsuser list', showout=False, force=True)
            except:
                continue

        if resp.find('admin') == -1:
            self.cuisine.core.run('jsuser add --data admin:%s:admin:admin@mail.com:cockpit' % passwd)
        else:
            self.cuisine.core.run('jsuser passwd -ul admin -up %s' % passwd)
