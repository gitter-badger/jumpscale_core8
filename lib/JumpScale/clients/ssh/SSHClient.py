from JumpScale import j

import paramiko
from paramiko.ssh_exception import SSHException, BadHostKeyException, AuthenticationException
import time
import io
import socket

import threading
import queue


class SSHClientFactory(object):

    def __init__(self):
        self.__jslocation__ = "j.clients.ssh"
        self.logger = j.logger.get("j.clients.ssh")
        self.cache = {}

    def get(self, addr, port=22, login="root", passwd=None, stdout=True, forward_agent=True, allow_agent=True, look_for_keys=True, timeout=5, testConnection=False, die=True):
        key = "%s_%s_%s_%s" % (addr, port, login, j.data.hash.md5_string(str(passwd)))
        if key not in self.cache:
            self.cache[key] = SSHClient(addr, port, login, passwd, stdout=stdout, forward_agent=forward_agent, allow_agent=allow_agent, look_for_keys=look_for_keys, timeout=timeout)
        if testConnection:
            ret = self.cache[key].connectTest(timeout=timeout, die=die)
            if ret is False:
                err = "Cannot connect over ssh:%s %s" % (addr, port)
                if die:
                    raise j.exceptions.RuntimeError(err)
                else:
                    self.logger.error(err)
                    return False

        return self.cache[key]

    def removeFromCache(self, client):
        key = "%s_%s_%s_%s" % (client.addr, client.port, client.login, j.data.hash.md5_string(str(client.passwd)))
        client.close()
        if key in self.cache:
            self.cache.pop(key)

    def getSSHKeyFromAgentPub(self, keyname="", die=True):
        rc, out = j.tools.cuisine.local.run("ssh-add -L", die=False)
        if rc > 1:
            err = "Error looking for key in ssh-agent: %s", out
            if die:
                raise j.exceptions.RuntimeError(err)
            else:
                self.logger.error(err)
                return None

        if keyname == "":
            paths = []
            for line in out.splitlines():
                line = line.strip()
                paths.append(line.split(" ")[-1])
            if len(paths) == 0:
                raise j.exceptions.RuntimeError("could not find loaded ssh-keys")

            path = j.tools.console.askChoice(paths, "Select ssh key to push (public part only).")
            keyname = j.sal.fs.getBaseName(path)

        for line in out.splitlines():
            delim = (".ssh/%s" % keyname)
            if line.endswith(delim):
                content = line.strip()
                content = content
                return content
        err = "Did not find key with name:%s, check its loaded in ssh-agent with ssh-add -l" % keyname
        if die:
            raise j.exceptions.RuntimeError(err)
        else:
            self.logger.error(err)
        return None

    def close(self):
        for key, client in self.cache.items():
            client.close()


class SSHClient(object):

    def __init__(self, addr, port=22, login="root", passwd=None, stdout=True, forward_agent=True, allow_agent=True, look_for_keys=True, timeout=5.0):
        self.port = port
        self.addr = addr
        self.login = login
        self.passwd = passwd
        self.stdout = stdout
        self._connection_ok = None
        if passwd is not None:
            self.forward_agent = False
            self.allow_agent = False
            self.look_for_keys = False
        else:
            self.forward_agent = forward_agent
            self.allow_agent = allow_agent
            self.look_for_keys = look_for_keys

        self.logger = j.logger.get("j.clients.ssh")

        self._transport = None
        self._client = None
        self._cuisine = None

    def _test_local_agent(self):
        """
        try to connect to the local ssh-agent
        return True if local agent is running, False if not
        """
        agent = paramiko.Agent()
        if len(agent.get_keys()) == 0:
            return False
        else:
            return True

    @property
    def transport(self):
        if self.client is None:
            raise j.exceptions.RuntimeError("Could not connect to %s:%s" % (self.addr, self.port))
        self._transport = self.client.get_transport()
        return self._transport

    @property
    def client(self):
        if self._client is None:
            self.logger.info('ssh new client to %s@%s:%s' % (self.login, self.addr, self.port))

            start = j.data.time.getTimeEpoch()
            timeout = 20
            while start + timeout > j.data.time.getTimeEpoch():
                try:
                    self._client = paramiko.SSHClient()
                    self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self._client.connect(self.addr, self.port, username=self.login, password=self.passwd, allow_agent=self.allow_agent, look_for_keys=self.look_for_keys, timeout=1)
                    break
                except:
                    self.reset()
                    time.sleep(1)
                    continue
            if self._client is None:
                raise j.exceptions.RuntimeError('Impossible to create SSH connection to %s:%s' % (self.addr, self.port))

        return self._client

    def reset(self):
        self._client = None
        self._transport = None

    def getSFTP(self):
        sftp = self.client.open_sftp()
        return sftp

    def connectTest(self, cmd="ls /", timeout=5, die=True):
        """
        will trying to connect over ssh & execute the specified command, timeout is in sec
        error will be raised if not able to do (unless if die set)\
        return False if not ok
        """
        if not self._connection_ok:
            self.logger.info("Test connection to %s:%s" % (self.addr, self.port))
            rc = 1
            start = j.data.time.getTimeEpoch()

            if j.sal.nettools.waitConnectionTest(self.addr, self.port, timeout) == False:
                self.logger.error("Cannot connect to ssh server %s:%s" % (self.addr, self.port))
                return False

            while start + timeout > j.data.time.getTimeEpoch() and rc != 0:
                try:
                    rc, out = self.execute(cmd, showout=False)
                except (BadHostKeyException, AuthenticationException) as e:
                    # cant' recover, no point to wait. exit now
                    self.logger.error("authentification error. abording connection")
                    self.logger.error(e)
                    rc = 1
                    break
                except (SSHException, socket.error) as e:
                    self.logger.error("Unexpected error. abording connection")
                    self.logger.error(e)
                    j.clients.ssh.removeFromCache(self)
                    self._client.close()
                    self.reset()
                    time.sleep(0.1)
                    continue

            if rc > 0:
                j.clients.ssh.removeFromCache(self)
                self._connection_ok = False
                err = "Could not connect to ssh on %s@%s:%s" % (self.login, self.addr, self.port)
                if die:
                    j.events.opserror_critical(err)
                else:
                    self.logger.error(err)
                return self._connection_ok
            else:
                self._connection_ok = True
        return self._connection_ok

    def execute(self, cmd, showout=True, die=True, combinestdr=True):
        """
        run cmd & return
        return: (retcode,out_err)
        """
        ch = self.transport.open_session()

        if self.forward_agent:
            paramiko.agent.AgentRequestHandler(ch)

        class StreamReader(threading.Thread):

            def __init__(self, stream, queue, flag):
                super(StreamReader, self).__init__()
                self.stream = stream
                self.queue = queue
                self.flag = flag
                self._stopped = False
                self.setDaemon(True)

            def run(self):
                """
                read until all buffers are empty and retrun code is ready
                """
                while not self.stream.closed and not self._stopped:
                    buf = ''
                    buf = self.stream.readline()
                    if len(buf) > 0:
                        self.queue.put((self.flag, buf))
                    elif not ch.exit_status_ready():
                        continue
                    elif self.flag == 'O' and ch.recv_ready():
                        continue
                    elif self.flag == 'E' and ch.recv_stderr_ready():
                        continue
                    else:
                        break
                self.queue.put(('T', self.flag))

        # execute the command on the remote server
        ch.exec_command(cmd)
        # indicate that we're not going to write to that channel anymore
        ch.shutdown_write()
        # create file like object for stdout and stderr to read output of command
        stdout = ch.makefile('r')
        stderr = ch.makefile_stderr('r')

        # Start stream reader thread that will read strout and strerr
        inp = queue.Queue()
        outReader = StreamReader(stdout, inp, 'O')
        errReader = StreamReader(stderr, inp, 'E')
        outReader.start()
        errReader.start()

        err = ""  # error buffer
        out = ""  # stdout buffer
        out_eof = False
        err_eof = False

        while out_eof is False or err_eof is False:
            try:
                chan, line = inp.get(block=True, timeout=1.0)
                if chan == 'T':
                    if line == 'O':
                        out_eof = True
                    elif line == 'E':
                        err_eof = True
                    continue
                if chan == 'O':
                    if showout:
                        print((line.strip()))
                    out += line
                elif chan == 'E':
                    if showout:
                        print((line.strip()))
                    err += line
            except queue.Empty:
                pass

        # stop the StreamReader and wait for the thread to finish
        outReader._stopped = True
        errReader._stopped = True
        outReader.join()
        errReader.join()

        # indicate that we're not going to read from this channel anymore
        ch.shutdown_read()
        # close the channel
        ch.close()

        # close all the pseudofiles
        stdout.close()
        stderr.close()

        retcode = ch.recv_exit_status()

        # can happend that some command only output on stderr but we still want to retreive the output.
        # if return code is valid we use stderr as output value
        if retcode == 0 and out == '' and len(err) > 0:
            out = err

        if retcode > 0:
            if die:
                raise j.exceptions.RuntimeError("Cannot execute (ssh):\n%s\noutput:\n%serrors:\n%s" % (cmd, out, err))
            else:
                self.logger.error(err)
                out = err

        return (retcode, out)

    def close(self):
        self.client.close()

    def rsync_up(self, source, dest, recursive=True):
        if dest[0] != "/":
            raise j.exceptions.RuntimeError("dest path should be absolute, need / in beginning of dest path")

        dest = "%s@%s:%s" % (self.login, self.addr, dest)
        j.sal.fs.copyDirTree(source, dest, keepsymlinks=True, deletefirst=False,
                             overwriteFiles=True, ignoredir=[".egg-info", ".dist-info", "__pycache__"], ignorefiles=[".egg-info"], rsync=True,
                             ssh=True, sshport=self.port, recursive=recursive)

    def rsync_down(self, source, dest, source_prefix="", recursive=True):
        if source[0] != "/":
            raise j.exceptions.RuntimeError("source path should be absolute, need / in beginning of source path")
        source = "%s@%s:%s" % (self.login, self.addr, source)
        j.sal.fs.copyDirTree(source, dest, keepsymlinks=True, deletefirst=False,
                             overwriteFiles=True, ignoredir=[".egg-info", ".dist-info"], ignorefiles=[".egg-info"], rsync=True,
                             ssh=True, sshport=self.port, recursive=recursive)

    @property
    def cuisine(self):
        if self._cuisine is None:
            executor = j.tools.executor.getSSHBased(self.addr, self.port, self.login, self.passwd)
            self._cuisine = executor.cuisine
        return self._cuisine

    def ssh_authorize(self, user, key):
        self.cuisine.ssh.authorize(user, key)
