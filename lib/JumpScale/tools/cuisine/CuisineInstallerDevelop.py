
from JumpScale import j





from ActionDecorator import ActionDecorator
class actionrun(ActionDecorator):
    def __init__(self,*args,**kwargs):
        ActionDecorator.__init__(self,*args,**kwargs)
        self.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.installerdevelop"


class CuisineInstallerDevelop():

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine

    @actionrun(action=True)
    def python(self):
        if self.cuisine.platformtype.osname=="debian":
            C="""
            libpython3.4-dev
            python3.4-dev
            """
        else:
            C="""
            libpython3.5-dev
            python3.5-dev
            """
        self.cuisine.package.multiInstall(C)

        C="""
        libffi-dev
        gcc
        make
        build-essential
        autoconf
        libtool
        pkg-config
        libpq-dev
        libsqlite3-dev
        #net-tools
        """
        self.cuisine.package.multiInstall(C)

    @actionrun(action=True)
    def pip(self):
        self.cuisine.installer.base()
        self.python()
        C="""
            #important remove olf pkg_resources, will conflict with new pip
            rm -rf /usr/lib/python3/dist-packages/pkg_resources
            cd $tmpDir/
            rm -rf get-pip.py
            wget https://bootstrap.pypa.io/get-pip.py
            """
        C=self.cuisine.core.args_replace(C)
        self.cuisine.core.run_script(C)
        C="cd $tmpDir/;python3 get-pip.py"
        C=self.cuisine.core.args_replace(C)
        self.cuisine.core.run(C)

    @actionrun(action=True)
    def installJS8Deps(self):
        #make sure base is done & env is clean
        self.cuisine.installer.base()

        self.python()
        self.pip(action=True)

        if not self.cuisine.core.isArch:
            #install brotli
            C="""
            cd $tmpDir/
            sudo rm -rf brotli/
            git clone https://github.com/google/brotli.git
            cd $tmpDir/brotli/
            python setup.py install
            # cd tests
            # make
            # cd ..
            cp $tmpDir/brotli/tools/bro /usr/local/bin/
            rm -rf $tmpDir/brotli
            """
            C=self.cuisine.core.args_replace(C)
            self.cuisine.core.run_script(C,force=False)

        #python etcd
        C="""
        cd $tmpDir/
        git clone https://github.com/jplana/python-etcd.git
        cd python-etcd
        python3 setup.py install
        """
        C=self.cuisine.core.args_replace(C)
        self.cuisine.core.run_script(C,force=False)

        #gevent
        C="""
        pip3 install 'cython>=0.23.4' git+git://github.com/gevent/gevent.git#egg=gevent
        """
        self.cuisine.core.run_script(C,force=False)

        C="""
        cffi==1.5.2
        paramiko

        msgpack-python
        redis
        #credis
        aioredis

        mongoengine==0.10.6

        certifi
        docker-py

        gitlab3
        gitpython
        html2text

        # pysqlite
        click
        influxdb
        ipdb
        ipython --upgrade
        jinja2
        netaddr
        wtforms_json

        reparted
        pytoml
        pystache
        pymongo
        psycopg2
        pathtools
        psutil

        pytz
        requests
        sqlalchemy
        urllib3
        zmq
        pyyaml
        python-etcd
        websocket
        marisa-trie
        pylzma
        ujson
        watchdog
        pygo
        pygithub
        minio

        # colorlog
        colored-traceback
        #pygments
        tmuxp

        xonsh
        pudb

        traitlets
        python-telegram-bot
        colorlog
        path.py
        """
        self.cuisine.pip.multiInstall(C,upgrade=True)


        if self.cuisine.platformtype.osname!="debian":
            C="""
            blosc
            bcrypt
            """
            self.cuisine.pip.multiInstall(C,upgrade=True)

        self.cuisine.apps.redis.install()

        """
        install dnspython3
        """
        self.dnspython3()

    @actionrun(action=True)
    def jumpscale8(self):
        if self.cuisine.installer.jumpscale_installed():
            return
        self.installJS8Deps()

        if self.cuisine.core.isUbuntu or self.cuisine.core.isArch:

            if self.cuisine.core.dir_exists("/usr/local/lib/python3.4/dist-packages"):
                linkcmd="mkdir -p /usr/local/lib/python3.5/dist-packages/JumpScale;ln -s /usr/local/lib/python3.5/dist-packages/JumpScale /usr/local/lib/python3.4/dist-packages/JumpScale"
                self.cuisine.core.run(linkcmd)            

            C='cd $tmpDir/;rm -f install.sh;curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/master/install/install.sh > install.sh;bash install.sh'
            C=self.cuisine.core.args_replace(C)
            self.cuisine.core.run(C)
        elif self.cuisine.core.isMac:
            cmd = """sudo mkdir -p /opt
            # sudo chown -R despiegk:root /opt
            ruby -e \"$ (curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\""""
            self.cuisine.core.run(cmd)
        else:
            raise j.exceptions.RuntimeError("platform not supported yet")


    @actionrun(action=True)
    def dnspython3(self):
        C = """
            cd $tmpDir
            wget http://www.dnspython.org/kits3/1.12.0/dnspython3-1.12.0.tar.gz
            tar -xf dnspython3-1.12.0.tar.gz
            cd dnspython3-1.12.0
            ./setup.py install
            """
        self.cuisine.core.run_script(C)
