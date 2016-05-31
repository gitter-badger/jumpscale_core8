
from JumpScale import j
import os

import socket

from ActionDecorator import ActionDecorator
class actionrun(ActionDecorator):
    def __init__(self,*args,**kwargs):
        ActionDecorator.__init__(self,*args,**kwargs)
        self.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.installer"


class CuisineInstaller:

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine

    @actionrun(action=True)
    def jumpscale_installed(self, die=False):
        rc, out = self.cuisine.core.run('which js8', die=False)
        if rc == 0 and out:
            return True
        return False

    @actionrun(action=True)
    def clean(self):
        self.cuisine.core.dir_ensure(self.cuisine.core.dir_paths["tmpDir"])
        if not self.cuisine.core.isMac:
            C = """
                set +ex
                # pkill redis-server #will now kill too many redis'es, should only kill the one not in docker
                # pkill redis #will now kill too many redis'es, should only kill the one not in docker
                umount -fl /optrw
                apt-get remove redis-server -y
                rm -rf /overlay/js_upper
                rm -rf /overlay/js_work
                rm -rf /optrw
                js8 stop
                pskill js8
                umount -f /opt
                """
        else:
            C = """
                set +ex
                js8 stop
                pskill js8
                echo "OK"
                """

        self.cuisine.core.run_script(C,die=False)


    @actionrun(action=True)
    def jumpscale8(self, rw=False, reset=False):
        """
        install jumpscale, will be done as sandbox

        @param rw if True install sandbox in RW mode
        @param reset, remove old code (only used when rw mode)

        """
        import time
        if self.jumpscale_installed() and not reset:
            return
        self.clean()
        self.base()


        C = """
            js8 stop
            set -ex
            cd /usr/bin
            rm -f js8
            cd /usr/local/bin
            rm -f js8
            rm -f /usr/local/bin/jspython
            rm -f /usr/local/bin/js
            rm -fr /opt/*
            """
        self.cuisine.core.run_script(C, action=True,force=True)

        if not self.cuisine.core.isUbuntu:
            raise j.exceptions.RuntimeError("not supported yet")

        if reset:
            C = """
                set +ex
                rm -rf /opt
                rm -rf /optrw
                """
            self.cuisine.core.run_script(C, action=True,force=True)
            

        C = """
            wget https://stor.jumpscale.org/storx/static/js8 -O /usr/local/bin/js8
            chmod +x /usr/local/bin/js8
            cd /
            mkdir -p $base
            """
        self.cuisine.core.run_script(C, action=True,force=True)

        """
        install jumpscale8 sandbox in read or readwrite mode
        """
        C = """
            set -ex
            rm -rf /opt
            cd /usr/local/bin
            """
        if rw:
            C += "./js8 -rw init"
        else:
            C += "./js8 init"
        self.cuisine.core.run_script(C, action=True,force=True)

        start = j.data.time.epoch
        timeout = 30
        while start + timeout > j.data.time.epoch:
            basejs8 = j.dirs.base
            if not self.cuisine.core.file_exists('{basedir}bin/jspython'.format(basedir=basejs8)):
                time.sleep(2)
            else:
                self.cuisine.core.file_link('{basedir}bin/jspython'.format(basedir=basejs8), '/usr/local/bin/jspython')
                self.cuisine.core.file_link('{basedir}bin/js'.format(basedir=basejs8), '/usr/local/bin/js')
                self.cuisine.bash.include('{basedir}env.sh'.format(basedir=basejs8))
                break

        print ("* re-login into your shell to have access to js, because otherwise the env arguments are not set properly.")

    @actionrun(action=True)
    def libvirt(self):
        """
        do not use in containers or VMs only actual machines @todo not tested 
        """
        #@todo need to check and exit if required (*1*)
        self.cuisine.package.install('libvirt-dev')
        self.cuisine.pip.install("libvirt-python==1.3.2", upgrade=False)
        
    @actionrun(action=True)
    def base(self):
        self.clean()

        if self.cuisine.core.isMac:
            C=""
        else:
            C="""
            sudo
            net-tools
            python3
            """

        C+="""
        openssl
        wget
        curl
        git
        mc
        tmux
        """
        out=""
        #make sure all dirs exist
        for key,item in self.cuisine.core.dir_paths.items():
            out+="mkdir -p %s\n"%item
        self.cuisine.core.run_script(out)

        if not self.cuisine.core.isMac:
            self.cuisine.package.install("fuse")

        if self.cuisine.core.isArch:
            self.cuisine.package.install("wpa_actiond") #is for wireless auto start capability
            self.cuisine.package.install("redis-server")

        self.cuisine.package.mdupdate()
        self.cuisine.package.multiInstall(C)
        self.cuisine.package.upgrade()
        self.cuisine.package.clean()


    @actionrun(action=True)
    def ftpserver(self,root="/storage/ftpserver",config="",port=2121):

        self.cuisine.fw.ufw_enable()
        self.cuisine.fw.allowIncoming(port)

        cmd="sudo ufw allow 50000:65535/tcp"
        self.cuisine.core.run(cmd)

        """
        example config 
            config='''
                home:
                  guest2: ['123456']
                  root: ['1234', elradfmwM]
                public:
                  guest: ['123456']
                  anonymous: []
            '''
        key is subpath in rootpath
        then users who have access

        cannot have same user in multiple dirs (shortcoming for now, need to investigate)

        . is home dir for user

        to set specific permissions is 2e element of list


        permissions
        ```
        Read permissions:
        "e" = change directory (CWD, CDUP commands)
        "l" = list files (LIST, NLST, STAT, MLSD, MLST, SIZE commands)
        "r" = retrieve file from the server (RETR command)
        Write permissions:

        "a" = append data to an existing file (APPE command)
        "d" = delete file or directory (DELE, RMD commands)
        "f" = rename file or directory (RNFR, RNTO commands)
        "m" = create directory (MKD command)
        "w" = store a file to the server (STOR, STOU commands)
        "M" = change mode/permission (SITE CHMOD command)
        ```

        """

        #DEBUG
        # config='''
        # home:
        #   guest2: ['123456']
        #   root: ['1234', elradfmwM]
        # public:
        #   guest: ['123456']
        #   anonymous: []
        # '''

        self.cuisine.installer.base()
        self.cuisine.pip.install("pyftpdlib")

        self.cuisine.btrfs.subvolumeCreate(root)

            # 
            # 

        if config=="":
            authorizer="    pyftpdlib.authorizers.UnixAuthorizer"
        else:
            authorizer=""
            configmodel=j.data.serializer.yaml.loads(config)
            for key,obj in configmodel.items():
                self.cuisine.btrfs.subvolumeCreate(j.sal.fs.joinPaths(root,key))
                for user,obj2 in obj.items():
                    if user.lower() == "anonymous":
                        authorizer+="    authorizer.add_anonymous('%s')\n"%j.sal.fs.joinPaths(root,key)
                    else:
                        if len(obj2)==1:
                            #no rights
                            rights="elradfmwM"
                            secret=obj2[0]
                        elif len(obj2)==2:
                            secret,rights=obj2
                        else:
                            raise j.exceptions.Input("wrong format in ftp config:%s, for user:%s"%(config,user))
                        authorizer+="    authorizer.add_user('%s', '%s', '%s', perm='%s')\n"%(user,secret,j.sal.fs.joinPaths(root,key),rights)

        C="""
        from pyftpdlib.authorizers import DummyAuthorizer
        from pyftpdlib.handlers import FTPHandler
        from pyftpdlib.servers import FTPServer

        def main():
            # Instantiate a dummy authorizer for managing 'virtual' users
            authorizer = DummyAuthorizer()

            # Define a new user having full r/w permissions and a read-only
            # anonymous user
        $authorizers

            # Instantiate FTP handler class
            handler = FTPHandler
            handler.authorizer = authorizer

            # Define a customized banner (string returned when client connects)
            handler.banner = "ftpd ready."

            # Specify a masquerade address and the range of ports to use for
            # passive connections.  Decomment in case you're behind a NAT.
            #handler.masquerade_address = '151.25.42.11'
            handler.passive_ports = range(60000, 65535)

            # Instantiate FTP server class and listen on 0.0.0.0:2121
            address = ('0.0.0.0', $port)
            server = FTPServer(address, handler)

            # set a limit for connections
            server.max_cons = 256
            server.max_cons_per_ip = 20

            # start ftp server
            server.serve_forever()

        if __name__ == '__main__':
            main()
        """
        C=j.data.text.strip(C)

        C=C.replace("$port",str(port))
        C=C.replace("$authorizers",authorizer)
        
        self.cuisine.core.dir_ensure("/etc/ftpserver")

        self.cuisine.core.file_write("/etc/ftpserver/start.py",C)


        self.cuisine.processmanager.ensure("polipo",cmd)

        self.cuisine.processmanager.ensure("pyftpserver","python3 /etc/ftpserver/start.py")


    def __str__(self):
        return "cuisine.installer:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))


    __repr__=__str__
