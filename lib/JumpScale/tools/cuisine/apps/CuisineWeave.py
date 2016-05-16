from JumpScale import j


from ActionDecorator import ActionDecorator


"""
please ensure that the start and build methods are separate and
the build doesnt place anyfile outside opt as it will be used in aysfs mounted system
"""


class actionrun(ActionDecorator):

    def __init__(self, *args, **kwargs):
        ActionDecorator.__init__(self, *args, **kwargs)
        self.selfobjCode = "cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.apps.weave"


class Weave():

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine

    @actionrun(action=True)
    def build(self, start=True, peer=None, jumpscalePath=True):
        if jumpscalePath:
            binPath = self.cuisine.core.joinpaths(
                self.cuisine.core.dir_paths['binDir'], 'weave')
        else:
            binPath = '/usr/local/bin/weave'
        self.cuisine.core.dir_ensure(j.sal.fs.getParent(binPath))

        C = '''
        curl -L git.io/weave -o {binPath} && sudo chmod a+x {binPath}
        '''.format(binPath=binPath)
        C = self.cuisine.core.args_replace(C)
        self.cuisine.docker.install()
        self.cuisine.package.ensure('curl')
        self.cuisine.core.run_script(C, profile=True)
        self.cuisine.bash.addPath(j.sal.fs.getParent(binPath), action=True)
        if start:
            self.start(peer)

    def start(self, peer=None):
        rc, out = self.cuisine.core.run("weave status", profile=True, die=False, showout=False)
        if rc != 0:
            cmd = 'weave launch'
            if peer:
                cmd += ' %s' % peer
            self.cuisine.core.run(cmd, profile=True)

        env = self.cuisine.core.run('weave env', profile=True)
        ss = env[len('export'):].strip().split(' ')
        for entry in ss:
            splitted = entry.split('=')
            if len(splitted) == 2:
                self.cuisine.bash.environSet(splitted[0], splitted[1])
            elif len(splitted) > 0:
                self.cuisine.bash.environSet(splitted[0], '')
