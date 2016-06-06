from JumpScale import j


from ActionDecorator import ActionDecorator


"""
please ensure that the start and build methods are separate and
the build doesnt place anyfile outside opt as it will be used in aysfs mounted system
"""


class actionrun(ActionDecorator):

    def __init__(self, *args, **kwargs):
        ActionDecorator.__init__(self, *args, **kwargs)
        self.selfobjCode = "cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.apps.influxdb"


class Influxdb:

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine

    @actionrun(action=True)
    def _build(self):
        self.cuisine.installer.base()

        if self.cuisine.core.isMac:
            self.cuisine.package.mdupdate()
            self.cuisine.package.install('influxdb')
        if self.cuisine.core.isUbuntu:
            self.cuisine.core.dir_ensure("$tmplsDir/cfg/influxdb")
            C= """
    cd $tmpDir
    wget https://s3.amazonaws.com/influxdb/influxdb-0.10.0-1_linux_amd64.tar.gz
    tar xvfz influxdb-0.10.0-1_linux_amd64.tar.gz
    cp influxdb-0.10.0-1/usr/bin/influxd $binDir
    cp influxdb-0.10.0-1/etc/influxdb/influxdb.conf $tmplsDir/cfg/influxdb/influxdb.conf"""
            C = self.cuisine.bash.replaceEnvironInText(C)
            C = self.cuisine.core.args_replace(C)
            self.cuisine.core.run_script(C, profile=True, action=True)
            self.cuisine.bash.addPath(self.cuisine.core.args_replace("$binDir"), action=True)

    def build(self, start=True):
        self._build()
        if start:
            self.start()

    def start(self):
        binPath = self.cuisine.bash.cmdGetPath('influxd')
        self.cuisine.core.dir_ensure("$varDir/data/influxdb")
        self.cuisine.core.dir_ensure("$varDir/data/influxdb/meta")
        self.cuisine.core.dir_ensure("$varDir/data/influxdb/data")
        self.cuisine.core.dir_ensure("$varDir/data/influxdb/wal")
        content = self.cuisine.core.file_read('$tmplsDir/cfg/influxdb/influxdb.conf')
        cfg = j.data.serializer.toml.loads(content)
        cfg['meta']['dir'] = "$varDir/data/influxdb/meta"
        cfg['data']['dir'] = "$varDir/data/influxdb/data"
        cfg['data']['wal-dir'] = "$varDir/data/influxdb/data"
        self.cuisine.core.dir_ensure('$cfgDir/influxdb')
        self.cuisine.core.file_write('$cfgDir/influxdb/influxdb.conf', j.data.serializer.toml.dumps(cfg))
        cmd = "%s -config $cfgDir/influxdb/influxdb.conf" % (binPath)
        self.cuisine.process.kill("influxdb")
        self.cuisine.processmanager.ensure("influxdb", cmd=cmd, env={}, path="")