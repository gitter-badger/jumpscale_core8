from JumpScale import j


from ActionDecorator import ActionDecorator


"""
please ensure that the start and build methods are separate and
the build doesnt place anyfile outside opt as it will be used in aysfs mounted system
"""

class actionrun(ActionDecorator):
    def __init__(self, *args, **kwargs):
        ActionDecorator.__init__(self, *args, **kwargs)
        self.selfobjCode = "cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.apps.controller"


class Controller:

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine

    @actionrun(action=True)
    def build(self, start=True):
        """
        config: https://github.com/g8os/controller.git
        """
        #deps
        self.cuisine.apps.installdeps()
        self.cuisine.apps.redis.build(start=False)
        self.cuisine.apps.mongodb.build(start=False)
        self.cuisine.apps.syncthing.build(start=False)


        self.cuisine.processmanager.remove("agentcontroller8")
        pm = self.cuisine.processmanager.get("tmux")
        pm.stop("syncthing")

        self.cuisine.core.dir_ensure("$tmplsDir/cfg/controller", recursive=True)

        #get repo
        url = "github.com/g8os/controller"
        self.cuisine.golang.godep(url)

        sourcepath = "$goDir/src/github.com/g8os/controller"

        #do the actual building
        self.cuisine.core.run("cd %s && go build ." % sourcepath, profile=True)

        #move binary
        self.cuisine.core.file_move("%s/controller" % sourcepath, "$binDir/controller")



        #file copy
        self.cuisine.core.dir_remove("$tmplsDir/cfg/controller/extensions")
        self.cuisine.core.file_copy("%s/github/jumpscale/jumpscale_core8/apps/agentcontroller/jumpscripts/jumpscale" % self.cuisine.core.dir_paths["codeDir"], "$tmplsDir/cfg/controller/jumpscripts/", recursive=True)
        self.cuisine.core.file_copy("%s/extensions" % sourcepath, "$tmplsDir/cfg/controller/extensions", recursive=True)

        if start:
            self.start()

    def start(self):
        import hashlib
        from xml.etree import ElementTree

        self.cuisine.core.dir_ensure("$cfgDir/controller/")
        self.cuisine.core.file_copy("$tmplsDir/cfg/controller", "$cfgDir/", recursive=True)

        # edit config
        sourcepath = "$goDir/src/github.com/g8os/controller"
        C = self.cuisine.core.file_read("%s/agentcontroller.toml" % sourcepath)
        cfg = j.data.serializer.toml.loads(C)

        cfgDir = self.cuisine.core.dir_paths['cfgDir']
        base=j.dirs.base
        cfg["events"]["python_path"] = self.cuisine.core.joinpaths(cfgDir, "/controller/extensions:{basedir}/lib".format(basedir=base))
        cfg["processor"]["python_path"] = self.cuisine.core.joinpaths(cfgDir, "/controller/extensions:/{basedir}lib".format(basedir=base))
        cfg["jumpscripts"]["python_path"] = self.cuisine.core.joinpaths(cfgDir, "/controller/extensions:{basedir}lib".format(basedir=base))
        cfg["jumpscripts"]["settings"]["jumpscripts_path"] = self.cuisine.core.joinpaths(cfgDir, "/controller/jumpscripts")
        C = j.data.serializer.toml.dumps(cfg)

        self.cuisine.core.file_write('$cfgDir/controller/agentcontroller.toml', C, replaceArgs=True)

        # expose syncthing and get api key
        sync_cfg = ElementTree.fromstring(self.cuisine.core.file_read("$tmplsDir/cfg/syncthing/config.xml"))
        sync_id = sync_cfg.find('device').get('id')

        #set address
        sync_cfg.find("./gui/address").text = '127.0.0.1:18384'

        jumpscripts_id = "jumpscripts-%s" % hashlib.md5(sync_id.encode()).hexdigest()
        jumpscripts_path = self.cuisine.core.args_replace("$cfgDir/controller/jumpscripts")

        #find folder element
        configured = False
        for folder in sync_cfg.findall('folder'):
            if folder.get('id') == jumpscripts_id:
                configured = True
                break

        if not configured:
            folder = ElementTree.SubElement(sync_cfg, 'folder', {
                'id': jumpscripts_id,
                'path': jumpscripts_path,
                'ro': 'true',
                'rescanIntervalS': '60',
                'ignorePerms': 'false',
                'autoNormalize': 'false'
            })

            ElementTree.SubElement(folder, 'device', {'id': sync_id})
            ElementTree.SubElement(folder, 'minDiskFreePct').text = '1'
            ElementTree.SubElement(folder, 'versioning')
            ElementTree.SubElement(folder, 'copiers').text = '0'
            ElementTree.SubElement(folder, 'pullers').text = '0'
            ElementTree.SubElement(folder, 'hashers').text = '0'
            ElementTree.SubElement(folder, 'order').text = 'random'
            ElementTree.SubElement(folder, 'ignoreDelete').text = 'false'

        dump = ElementTree.tostring(sync_cfg, 'unicode')
        j.logger.log("SYNCTHING CONFIG", level=10)
        j.logger.log(dump, level=10)
        self.cuisine.core.file_write("$cfgDir/syncthing/config.xml", dump)

        # start
        self.cuisine.apps.syncthing.start()
        self.cuisine.apps.mongodb.start()
        self.cuisine.apps.redis.start()
        env = {}
        env["TMPDIR"] = self.cuisine.core.dir_paths["tmpDir"]
        cmd = "$binDir/controller -c $cfgDir/controller/agentcontroller.toml"
        pm = self.cuisine.processmanager.get("tmux")
        pm.ensure("controller", cmd=cmd, path="$cfgDir/controller/", env=env)
