from JumpScale import j
# import JumpScale.sal.tmux
import os
import signal
import inspect


class ActionsBaseNode:
    """
    actions which can be executed remotely on node
    """

    def installFiles(self):

        #@todo (*1*) I think is not optimally designed, or we work with fuse or without
        #if without we need to create a library function on e.g. AYSFS which allows someone to connect to G8OS Stor
        #and then call this library to expand the content locally, this should be done through arguments  ($...)

        from urllib.error import HTTPError

        key = "$(service.name)__$(service.instance)"
        flist = '%s.flist' % key

        tmpDir = j.sal.fs.getTmpDirPath()
        j.sal.fs.createDir(tmpDir)
        mdPath = j.sal.fs.joinPaths(tmpDir, flist)

        for client in j.atyourservice.findServices(role='ays_stor_client'):
            if client.name == 'ays_stor_client.http':

                addr = client.hrd.getStr('http.url')
                url = '%s/dedupe/md/%s' % (addr, flist)
                conn = j.clients.http.getConnection()
                try:
                    conn.download(url, mdPath)
                except HTTPError as err:
                    print("Can't download flist file from %s: %s" % (url, err))
                    continue # try from another client

                content = j.sal.fs.fileGetContents(mdPath)
                for line in content.splitlines():
                    path, hash, size = line.split("|")
                    j.sal.fs.createDir(j.sal.fs.getParent(path))

                    if j.sal.fs.exists(path):
                        # don't donwload if we already have the file
                        if j.data.hash.md5(path) == hash:
                            continue

                    url = "%s/dedupe/files/%s/%s/%s" %(addr, hash[0], hash[1], hash)
                    value, unit = j.data.units.bytes.converToBestUnit(int(size)) #@todo typo?  (*1*)
                    print("downloading %s (%s %s)" % (path, value, unit))
                    unit = unit if unit != '' else 'B'
                    conn.download(url, path)

                    # @TODO need a way to know if the file need to be executable or not
                    j.sal.fs.chmod(path, 0o775)

                break

            elif client.name == 'ays_stor_client.ssh':
                addr = client.hrd.getStr('ip')
                port = client.hrd.getInt('ssh.port')
                root = client.hrd.getStr('root')
                src = '%s:%s/dedupe/md/%s' % (addr, root, flist)
                j.sal.fs.copyDirTree(src, mdPath, deletefirst=True, overwriteFiles=True, ssh=True, sshport=port, recursive=False)

                content = j.sal.fs.fileGetContents(mdPath)
                for line in content.splitlines():
                    path, hash, size = line.split("|")
                    j.sal.fs.createDir(j.sal.fs.getParent(path))

                    if j.sal.fs.exists(path):
                        # don't donwload if we already have the file
                        if j.data.hash.md5(path) == hash:
                            continue

                    src = "%s:%s/dedupe/files/%s/%s/%s" % (addr, root, hash[0], hash[1], hash)
                    value, unit = j.data.units.bytes.converToBestUnit(int(size))
                    unit = unit if unit != '' else 'B'
                    print("downloading %s (%s %s)" % (path, value, unit))
                    j.sal.fs.copyDirTree(src, path, deletefirst=False, overwriteFiles=False, ssh=True, sshport=port, recursive=False)

                    # @TODO need a way to know if the file need to be executable or not
                    j.sal.fs.chmod(path, 0o775)

                break

    def _installFromAysFS(self):
        j.sal.process.killProcessByName('aysfs', 10)

    def install(self):

        if j.sal.process.checkProcessRunning('aysfs'):
            self._installFromAysFS(self.service)

        if len(j.atyourservice.findServices(role='ays_stor_client')) > 0:
            self._installFromStore(self.service)

        # else:
            # j.events.opserror_critical("Can't find any means to install the service. Please enable AYSFS or consume a store_client")

    def prepare(self):
        """
        this gets executed before the files are downloaded & installed on approprate spots
        this gets done remotely
        typically used to prepare a system e.g. make sure appropriate updates or packages installed
        the next step will copy files from the recipe's to the destination locations on the target (if binary git repo's used)
        """
        if 'ubuntu' in j.core.platformtype.myplatform.platformtypes:

            for src in self.service.hrd_template.getListFromPrefix("ubuntu.apt.source"):
                src = src.replace(";", ":")
                if src.strip() != "":
                    j.sal.ubuntu.apt_sources_uri_add(src)

            for src in self.service.hrd_template.getListFromPrefix("ubuntu.apt.key.pub"):
                src = src.replace(";", ":")
                if src.strip() != "":
                    cmd = "wget -O - %s | apt-key add -" % src
                    j.sal.process.execute(cmd, die=False)

            if self.service.hrd_template.getBool("ubuntu.apt.update", default=False):
                log("apt update")
                j.sal.process.execute("apt-get update -y", die=False)

            if self.service.hrd_template.getBool("ubuntu.apt.upgrade", default=False):
                j.sal.process.execute("apt-get upgrade -y", die=False)

            if self.service.hrd_template.exists("ubuntu.packages"):
                packages = self.service.hrd_template.getList("ubuntu.packages")
                packages = [pkg.strip() for pkg in packages if pkg.strip() != ""]
                if packages:
                    j.sal.ubuntu.apt_install(" ".join(packages))
                    # j.sal.process.execute("apt-get install -y -f %s" % " ".join(packages), die=True)
        return True

    def _getDomainName(self, process):
        domain = self.service.domain
        if process["name"] != "":
            name = process["name"]
        else:
            name = self.service.name
            if self.service.instance != "main":
                name += "__%s" % self.service.instance
        return domain, name

    def start(self):
        """
        start happens because of info from main.hrd file but we can overrule this
        make sure to also call ActionBase.start(self.service) in your implementation otherwise the default behavior will not happen

        only use when you want to overrule

        """
        if self.service.getProcessDicts()==[]:
            return

        def start2(process, nbr=None):

            cwd=process["cwd"]
            # args['process'] = process
            if nbr is None:
                self.stop()

            tcmd=process["cmd"]
            if tcmd=="jspython":
                tcmd="source %s/env.sh;jspython"%(j.dirs.base)

            targs=process["args"]
            tuser=process["user"]
            if tuser=="":
                tuser="root"
            tlog=self.service.hrd.getBool("process.log",default=True)
            env=process["env"]

            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(process)
            if nbr is not None:
                name = "%s.%d" % (name, i)
            log("Starting %s:%s" % (domain, name))

            if startupmethod == 'upstart':
                # check if we are in our docker image which uses myinit instead of upstart
                if j.sal.fs.exists(path="/etc/my_init.d/"):
                    cmd2="%s %s"%(tcmd,targs)
                    extracmds=""
                    if cmd2.find(";")!=-1:
                        parts=cmd2.split(";")
                        extracmds="\n".join(parts[:-1])
                        cmd2=parts[-1]

                    C="#!/bin/sh\nset -e\ncd %s\nrm -f /var/log/%s.log\n%s\nexec %s >>/var/log/%s.log 2>&1\n"%(cwd,name,extracmds,cmd2,name)
                    j.sal.fs.remove("/var/log/%s.log"%name)
                    j.sal.fs.createDir("/etc/service/%s"%name)
                    path2="/etc/service/%s/run"%name
                    j.sal.fs.writeFile(path2, C)
                    j.sal.fs.chmod(path2,0o770)
                    j.sal.process.execute("sv start %s"%name,die=False, outputToStdout=False,outputStderr=False, captureout=False)
                else:
                    j.sal.ubuntu.service_install(name, tcmd, pwd=cwd, env=env)
                    j.sal.ubuntu.service_start(name)

            elif startupmethod=="tmux":
                j.tools.cuisine.local.tmux.executeInScreen(domain,name,tcmd+" "+targs,cwd=cwd, env=env,user=tuser)#, newscr=True)

            else:
                raise j.exceptions.RuntimeError("startup method not known or disabled:'%s'"%startupmethod)



                # if msg=="":
                #     pids=self.getPids(ifNoPidFail=False,wait=False)
                #     if len(pids) != self.numprocesses:
                #         msg="Could not start, did not find enough running instances, needed %s, found %s"%(self.numprocesses,len(pids))

                # if msg=="" and pids!=[]:
                #     for pid in pids:
                #         test=j.sal.process.isPidAlive(pid)
                #         if test==False:
                #             msg="Could not start, pid:%s was not alive."%pid

                # if log!="":
                #     msg="%s\nlog:\n%s\n"%(msg,log)

                # self.raiseError(msg)
                # return

        isrunning = self.check_up(wait=False)
        if isrunning:
            return

        processes = self.service.getProcessDicts()
        for i, process in enumerate(processes):

            if "platform" in process:
                if not j.core.platformtype.myplatform.checkMatch(process["platform"]):
                    continue
            if len(processes) > 1:
                start2(process, nbr=i)
            else:
                start2(process)

        isrunning = self.check_up()
        if isrunning is False:
            msg=""

            if self.service.getTCPPorts()==[0]:
                print('Done ...')
            elif self.service.getTCPPorts()!=[]:
                ports=",".join([str(item) for item in self.service.getTCPPorts()])
                msg="Could not start:%s, could not connect to ports %s."%(self.service,ports)
                j.events.opserror_critical(msg,"service.start.failed.ports")
            else:
                j.events.opserror_critical("could not start:%s"%self.service,"service.start.failed.other")

    def stop(self):
        """
        if you want a gracefull shutdown implement this method
        a uptime check will be done afterwards (local)
        return True if stop was ok, if not this step will have failed & halt will be executed.
        """

        if self.service.getProcessDicts()==[]:
            return

        def stop_process(process, nbr=None):
            # print "stop processs:%s"%process

            currentpids = (os.getpid(), os.getppid())
            for pid in self._get_pids([process]):
                if pid not in currentpids :
                    try:
                        j.sal.process.kill(-pid, signal.SIGTERM)
                    except Exception as e:
                        if e.message.find('Could not kill process with id %s.' % -pid) != -1:
                            j.sal.process.kill(pid, signal.SIGTERM)


            startupmethod=process["startupmanager"]
            domain, name = self._getDomainName(process)
            log("Stopping %s:%s" % (domain, name))
            if nbr is not None:
                name = "%s.%d" % (name, i)

            if j.sal.fs.exists(path="/etc/my_init.d/%s"%name):
                print("stop through myinitd:%s"%name)
                j.sal.process.execute("sv stop %s"%name,die=False, outputToStdout=False,outputStderr=False, captureout=False)
            elif startupmethod == "upstart":
                print("stop through upstart:%s"%name)
                j.sal.ubuntu.service_stop(name)
            elif startupmethod=="tmux":
                print("stop tmux:%s %s"%(domain,name))

                for tmuxkey,tmuxname in list(j.tools.cuisine.local.tmux.getWindows(domain).items()):
                    if tmuxname==name:
                        print("tmux kill:%s %s"%(tmuxkey,tmuxname))
                        j.tools.cuisine.local.tmux.killWindow(domain,name)
                        # print "killdone"

        if "$(service.name)" == 'redis':
            j.logger.redislogging = None
            j.logger.redis = None

        processes = self.service.getProcessDicts()
        if processes:
            for i, process in enumerate(processes):
                if len(processes) > 1:
                    stop_process(process, nbr=i)
                else:
                    stop_process(process)

        print("stop ok")


        return True

    def _get_pids(self, processes=None, **kwargs):
        pids = set()
        if processes is None:
            processes = self.service.getProcessDicts()
        for process in processes:
            for port in self.service.getTCPPorts(process):
                pids.update(j.sal.process.getPidsByPort(port))
            if process.get('filterstr', None):
                pids.update(j.sal.process.getPidsByFilter(process['filterstr']))
        return list(pids)

    def halt(self):
        """
        hard kill the app, std a linux kill is used, you can use this method to do something next to the std behavior
        """
        currentpids = (os.getpid(), os.getppid())
        for pid in self._get_pids():
            if pid not in currentpids :
                j.sal.process.kill(pid, signal.SIGKILL)
        if not self.check_down(self.service):
            j.events.opserror_critical("could not halt:%s"%self,"service.halt")
        return True

    def check_up(self, wait=True):
        """
        do checks to see if process(es) is (are) running.
        this happens on system where process is
        """
        def do(process, nbr=None):
            startupmethod = process["startupmanager"]
            if startupmethod == 'upstart':
                domain, name = self._getDomainName(process)
                if nbr is not None:
                    name = "%s.%d" % (name, i)
                # check if we are in our docker image which uses myinit instead of upstart
                if j.sal.fs.exists(path="/etc/my_init.d/"):
                    _, res, _ = j.sal.process.execute("sv status %s" % name, die=False,
                                             outputToStdout=False, outputStderr=False, captureout=True)
                    if res.startswith('ok'):
                        return True
                    else:
                        return False
                else:
                    return j.sal.ubuntu.service_status(name)
            else:
                ports = self.service.getTCPPorts()
                timeout = process["timeout_start"]
                if timeout == 0:
                    timeout = 2
                if not wait:
                    timeout = 0
                if len(ports) > 0:

                    for port in ports:
                        # need to do port checks
                        if wait:
                            if j.sal.nettools.waitConnectionTest("localhost", port, timeout)==False:
                                return False
                        elif j.sal.nettools.tcpPortConnectionTest('127.0.0.1', port) == False:
                                return False
                else:
                    # no ports defined
                    filterstr=process["filterstr"].strip()

                    if filterstr=="":
                        raise j.exceptions.RuntimeError("Process filterstr cannot be empty.")

                    start = j.data.time.getTimeEpoch()
                    now = start
                    while now <= start+timeout:
                        if j.sal.process.checkProcessRunning(filterstr):
                            return True
                        now = j.data.time.getTimeEpoch()
                    return False
        processes = self.service.getProcessDicts()
        for i, process in enumerate(processes):
            if len(processes) > 1:
                result = do(process, nbr=i)
            else:
                result = do(process)

            if result is False:
                domain, name = self._getDomainName(process)
                log("Status %s:%s not running" % (domain, name))
                return False
        log("Status %s is running" % (self.service))
        return True

    def check_down(self, wait=True):
        """
        do checks to see if process(es) are all down
        this happens on system where process is
        return True when down
        """
        print("check down local:%s"%self.service)
        def do(process):
            if not self.service.hrd.exists("process.cwd"):
                return

            ports=self.service.getTCPPorts()

            if len(ports)>0:
                timeout=process["timeout_stop"]
                if timeout==0:
                    timeout=2
                for port in ports:
                    #need to do port checks
                    if j.sal.nettools.waitConnectionTestStopped("localhost", port, timeout)==False:
                        return False
            else:
                #no ports defined
                filterstr=process["filterstr"].strip()
                if filterstr=="":
                    raise j.exceptions.RuntimeError("Process filterstr cannot be empty.")
                return j.sal.process.checkProcessRunning(filterstr)==False

        for process in self.service.getProcessDicts():
            result=do(process)
            if result==False:
                return False
        return True

    def build(self, build_server=None, image_build=False, image_push=False,debug=True,syncLocalJumpscale=False):
        """
        build_server : node service where the the service will be build
        """
        log("build")


        if debug:
            syncLocalJumpscale=True

        if build_server is None:
            self.actions.build(self)
            return

        build_host = None
        if j.data.types.string.check(build_server):
            domain, name, instance, role = j.atyourservice._parseKey(build_server)
            build_host = j.atyourservice.getService(domain=domain, name=name, instance=instance, role=role)
        else:
            build_host = build_server

        build_info = self.hrd_template.getDict('build')
        image = build_info['image']
        repo = build_info['repo']
        if 'dedupe_ns' in build_info:
            dedupe_ns = build_info['dedupe_ns']
        else:
            dedupe_ns = "dedupe"

        error=""

        try:
            # make sure to clean old service that could still be in the ays_repo
            j.atyourservice.remove(name='docker_build', instance=self.name)

            data = {
                'docker.build.repo': repo,
                'docker.image': image,
                'docker.build': image_build,
                'docker.upload': image_push,
            }
            print("init docker_build")
            docker_build = j.atyourservice.new(name='docker_build', instance=self.name, args=data, parent=build_host)

            print("deploy docker on build server %s" % build_host)
            j.atyourservice.apply()  # deploy docker in build server

            docker_addr = docker_build.hrd.getStr("tcp.addr")
            docker_port = docker_build.hrd.getStr("ssh.port")

            # remove key from know hosts, cause this is liklely that the key will change at each build because
            # we hit a newly created docker container each time.
            j.sal.process.execute('ssh-keygen -f "/root/.ssh/known_hosts" -R [%s]:%s' % (docker_addr, docker_port))

            dockerExecutor = j.tools.executor.getSSHBased(docker_addr, docker_port)
            # clean service tempates in docker to be sure we have the local version.
            if dockerExecutor.cuisine.core.dir_exists(self.path):
                dockerExecutor.cuisine.core.dir_remove(self.path, recursive=True)
            # upload local template inside the docker.
            dockerExecutor.upload(self.path, self.path)

            if syncLocalJumpscale:
                print ("upload jumpscale core lib to build docker.")
                dockerExecutor.upload("/opt/code/github/jumpscale/jumpscale_core8/lib/","/opt/code/github/jumpscale/jumpscale_core8/lib/")

            print("start build of %s" % self)
            dockerExecutor.execute("ays build -n %s" % self.name)

            # push metadata and flist to stores
            for client in j.atyourservice.findServices(name='ays_stor_client.ssh'):
                if client.hrd.exists('tcp.addr'):
                    ip = client.hrd.getStr('tcp.addr')
                else:
                    ip = client.hrd.getStr('ip')

                store_path = client.hrd.getStr('root')
                store_path = j.tools.path.get(store_path).joinpath(dedupe_ns)
                dest = "%s:%s" % (ip, store_path)
                # dockerExecutor.execute('mkdir -p %s' % store_path)

                cmd = 'rsync -rP /tmp/aysfs/files/ %s' % dest
                print('push metadata and flist to %s' % dest)
                dockerExecutor.execute(cmd)

            print('download flist file back into template directory')
            dockerExecutor.download("/tmp/aysfs/md/*", self.path)
        except Exception as e:
            error=j.errorconditionhandler.parsePythonExceptionObject(e)
            eco.getBacktraceDetailed()
        finally:
            if debug==False:
                docker_build.stop()
                docker_build.removedata()
                j.atyourservice.remove(name=docker_build.name, instance=docker_build.instance)
            if error!="":
                error="Could not build:%s\n%s"%(self,error)
                j.events.opserror_critical(error,"ays.build")