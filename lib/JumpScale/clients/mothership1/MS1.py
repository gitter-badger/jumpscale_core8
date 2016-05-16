import requests
from requests.exceptions import SSLError
import time
from JumpScale import j
# import JumpScale.lib.cloudrobots

# import JumpScale.baselib.redis2

import sys


class Output(object):
    def __init__(self):
        self.out=""
        self.lastlines=""
        self.counter=0

    def _write(self):
        self.lastlines=self.lastlines.replace("\n\n","\n")
        self.lastlines=self.lastlines.replace("\n\n","\n")
        self.lastlines=self.lastlines.replace("\n\n","\n")
        self.ms1.action.sendUserMessage(self.lastlines)
        self.lastlines=""
        self.counter=0

    def write(self, buf,**args):
        if self.lastlines.find(buf)==-1:
            self.lastlines+="%s\n"%buf
            if self.counter>20:
                self._write()
            if len(self.lastlines.split("\n"))>20:
                self._write()
            self.counter+=1

    def isatty(self):
        return False

    def flush(self):
        return None


class MS1Factory(object):
    def __init__(self):
        self.__jslocation__ = "j.clients.ms1"

    def get(self, apiURL='www.mothership1.com', port=443):
        return MS1(apiURL, port)


class MS1(object):

    def __init__(self, apiURL, port):
        self.apiURL = apiURL
        self.apiPort = port
        self.secret = ''
        self.IMAGE_NAME = 'Ubuntu 14.04'
        # self.redis_cl = j.clients.redis.getByInstance('system')
        self.stdout=Output()
        self.stdout.ms1=self
        self.stdout.prevout=sys.stdout
        self.action=None
        self.vars={}
        self.db = j.servers.kvs.getFSStore("/tmp/ms1.db")


    def getCloudspaceObj(self, space_secret,**args):
        if not self.db.exists('cloudrobot:cloudspaces:secrets', space_secret):
            raise j.exceptions.RuntimeError("E:Space secret does not exist, cannot continue (END)")
        space=j.data.serializer.json.loads(self.db.get('cloudrobot:cloudspaces:secrets', space_secret))
        return space

    def getCloudspaceId(self, space_secret):
        space=self.getCloudspaceObj(space_secret)
        return space["id"]

    def getCloudspaceSecret(self, login, password, cloudspace_name, location='default', spacesecret=None,**args):
        """
        @param location ca1 (canada),us2 (us)
        """
        baseURL = "%s:%s" % (self.apiURL,self.apiPort)
        params = {'username': login, 'password': password}
        try:
            response = requests.post('https://%s/restmachine/cloudapi/users/authenticate' % baseURL, params=params)
        except SSLError:
            response = requests.post('http://%s/restmachine/cloudapi/users/authenticate' % baseURL, params=params)

        if response.status_code != 200:
            raise j.exceptions.RuntimeError("E:Could not authenticate user %s" % login)
        auth_key = response.json()
        params = {'authkey': auth_key}
        try:
            response = requests.post('https://%s/restmachine/cloudapi/cloudspaces/list' % baseURL, params=params)
        except SSLError:
            response = requests.post('http://%s/restmachine/cloudapi/cloudspaces/list' % baseURL, params=params)

        cloudspaces = response.json()

        cloudspace = [cs for cs in cloudspaces if cs['name'] == cloudspace_name and cs['location'] == location]
        if cloudspace:
            cloudspace = cloudspace[0]
        else:
            raise j.exceptions.RuntimeError("E:Could not find a matching cloud space with name %s and location %s" % (cloudspace_name, location))

        self.db.set('cloudrobot:cloudspaces:secrets', auth_key,j.data.serializer.json.dumps(cloudspace))

        return auth_key

    def sendUserMessage(self,msg,level=2,html=False,args={}):
        if self.action!=None:
            self.action.sendUserMessage(msg,html=html)
        else:
            print(msg)

    def getApiConnection(self, space_secret,**args):
        # host = self.apiURL # if cs["location"] == 'ca1' else '%s.mothership1.com' % cs["location"]
        try:
            api=j.clients.portal.get(self.apiURL, self.apiPort, space_secret)
        except Exception as e:
            raise j.exceptions.RuntimeError("E:Could not login to MS1 API.")

        return api

    # def deployAppDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, aysdomain='solutions', aysname=None, config=None, description=None,**args):
    #     machine_id = self.deployMachineDeck(spacesecret, name, memsize, ssdsize, vsansize, description)
    #     api = self.getApiConnection(location)
    #     portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
    #     cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
    #     machines_actor = api.getActor('cloudapi', 'machines')
    #     # create ssh port-forward rule
    #     for _ in range(30):
    #         machine = machines_actor.get(machine_id)
    #         if j.data.types.ipaddress.check(machine['interfaces'][0]['ipAddress']):
    #             break
    #         else:
    #             time.sleep(2)
    #     if not j.data.types.ipaddress.check(machine['interfaces'][0]['ipAddress']):
    #         raise j.exceptions.RuntimeError('Machine was created, but never got an IP address')
    #     cloudspace_forward_rules = portforwarding_actor.list(machine['cloudspaceid'])
    #     public_ports = [rule['publicPort'] for rule in cloudspace_forward_rules]
    #     ssh_port = '2222'
    #     cloudspace = cloudspaces_actor.get(machine['cloudspaceid'])
    #     while True:
    #         if ssh_port not in public_ports:
    #             portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], ssh_port, machine['id'], '22')
    #             break
    #         else:
    #             ssh_port = str(int(ssh_port) + 1)

    #     # do an ssh connection to the machine
    #     if not j.sal.nettools.waitConnectionTest(cloudspace['publicipaddress'], int(ssh_port), 60):
    #         raise j.exceptions.RuntimeError("Failed to connect to %s %s" % (cloudspace['publicipaddress'], ssh_port))
    #     ssh_connection = j.remote.cuisine.api
    #     username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
    #     ssh_connection.fabric.api.env['password'] = password
    #     ssh_connection.fabric.api.env['connection_attempts'] = 5
    #     ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], ssh_port), username)

    #     # install ays there
    #     ssh_connection.sudo('ays mdupdate')
    #     if config:
    #         ays_hrd_file = j.sal.fs.joinPaths(j.dirs.hrdDir, '%s_%s' % (aysdomain, aysname))
    #         ssh_connection.file_write(ays_hrd_file, config, sudo=True)
    #     if aysdomain and aysname:
    #         ssh_connection.sudo('ays install -n %s -d %s' % (aysname, aysdomain))

    #     #cleanup
    #     cloudspace_forward_rules = portforwarding_actor.list(machine['cloudspaceid'])
    #     ssh_rule_id = [rule['id'] for rule in cloudspace_forward_rules if rule['publicPort'] == ssh_port][0]
    #     portforwarding_actor.delete(machine['cloudspaceid'], ssh_rule_id)
    #     if config:
    #         hrd = j.data.hrd.get(content=config)
    #         if hrd.exists('services_ports'):
    #             ports = hrd.getList('services_ports')
    #             for port in ports:
    #                 portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], str(port), machine['id'], str(port))
    #     return {'publicip': cloudspace['publicipaddress']}

    def getMachineSizes(self,spacesecret, cloudspaceId):
        if self.db.exists("ms1", "ms1:cache:%s:sizes"%spacesecret):
            return j.data.serializer.json.loads(self.db.get('ms1', "ms1:cache:%s:sizes"%spacesecret))
        api = self.getApiConnection(spacesecret)
        #sizes_actor = api.getActor('cloudapi', 'sizes')
        try:
            sizes = api.cloudapi.sizes.list(cloudspaceId=cloudspaceId)
        except TypeError:
            sizes = api.cloudapi.sizes.list()
        self.db.set("ms1", "ms1:cache:%s:sizes"%spacesecret,j.data.serializer.json.dumps(sizes))
        return sizes

    def createMachine(self, spacesecret, name, memsize=1024, ssdsize=None, vsansize=0, description='',
                      imagename="ubuntu.14.04.x64",delete=False, sshkey=None, hostname="", stackId=None,datadisks=None,**args):
        """
        memsize  # size is 512, 1024, 2048, 4096, 8192, 16384
        ssdsize  # if not passed along, will get the first size of the image's supported sizes
        imagename= fedora,windows,ubuntu.13.10,ubuntu.12.04,windows.essentials,ubuntu.14.04.x64
                   zentyal,debian.7,arch,fedora,centos,opensuse,gitlab,ubuntu.jumpscale

        sshkey = is content of pub key or path
        hostname if "" then will be same as name
        stack stackId where to create the vm. if not None
              the vm will be created on this stack. otherwise best stack will be choosen automaticly
        """
        if delete:
            self.deleteMachine(spacesecret, name)

        self.vars = {}

        if sshkey:
            if j.sal.fs.exists(path=sshkey):
                if sshkey.find(".pub") == -1:
                    raise j.exceptions.Input("public key path needs to have .pub at the end.")
                sshkey = j.sal.fs.fileGetContents(sshkey)

        api = self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        images = self.listImages(spacesecret)

        if imagename not in list(images.keys()):
            raise j.exceptions.Input("Imagename '%s' not in available images: '%s'" % (imagename, images))

        sizes = self.getMachineSizes(spacesecret, cloudspace_id)
        ssdsizes = {s: size['id'] for size in sizes for s in size['disks']}
        memsizes = set([size['memory'] for size in sizes])

        if not ssdsize:
            minsize = images[imagename][2]
            for size in ssdsizes.keys():
                if size >= minsize:
                    ssdsize = size
                    break
        else:
            ssdsize = int(ssdsize)

        if not ssdsize:
            raise j.exceptions.Input("No supported size found")

        try:
            memsize = int(memsize)
        except:
            # support for 0.5 memsize
            memsize = float(memsize)

        if memsize not in memsizes:
            raise j.exceptions.RuntimeError("E: supported memory sizes are %s, you specified:%s" % (', '.join(memsizes), memsize))
        if ssdsize not in ssdsizes:
            raise j.exceptions.RuntimeError("E: supported ssd sizes are %s (is in GB), you specified:%s" % (', '.join(ssdsizes), ssdsize))

        size_id = None
        for size in sizes:
            if size['memory'] == memsize:
                size_id = size['id']
                break

        if not size_id:
            raise j.exceptions.RuntimeError('E:Could not find a matching memory size %s' % memsize)

        if stackId is not None:
            machine_cb_actor = api.cloudbroker.machine
        self.vars["cloudspace.id"] = cloudspace_id
        self.vars["machine.name"] = name

        templateid = images[imagename][0]
        self.sendUserMessage("create machine: %s" % (name))

        if stackId and machine_cb_actor:
            # we want to deploy on a specific stack
            def valid():
                machines = machine_cb_actor.list(cloudspaceId=cloudspace_id)
                names = []
                for m in machines:
                    if m['status'] != 'DESTROYED':
                        names.append(m['name'])
                if name in names:
                    raise j.exceptions.Input("Could not create machine it does already exist.","ms1.createmachine.exists")

                    return False
                cloudspaceObj = api.cloudapi.cloudspaces.get(cloudspaceId=cloudspace_id)
                if cloudspaceObj['status'] not in ['DEPLOYED', 'VIRTUAL']:
                    raise j.exceptions.Input("Could not create machine it does already exist.","ms1.createmachine.exists")
                    return False
                return True

            if valid():
                try:
                    machine_id = machine_cb_actor.createOnStack(cloudspaceId=cloudspace_id, name=name, description=description, sizeId=size_ids[0], imageId=templateid, disksize=int(ssdsize), stackid=stackId, datadisks=datadisks)
                except Exception as e:
                    j.events.opserror_critical("Could not create machine on stack %s, unknown error : %s." % (stackId, e.message), "ms1.createmachine.exists")
        else:
            try:
                machine_id = api.cloudapi.machines.create(cloudspaceId=cloudspace_id, name=name, description=description, \
                    sizeId=size_id, imageId=templateid, disksize=int(ssdsize), datadisks=datadisks)
            except Exception as e:
                if str(e).find("Selected name already exists") != -1:
                   raise j.exceptions.Input("Could not create machine it does already exist.","ms1.createmachine.exists")
                raise j.exceptions.RuntimeError("E:Could not create machine, unknown error : %s", e.response.content)

        self.vars["machine.id"] = machine_id

        self.sendUserMessage("machine created")
        self.sendUserMessage("find free ipaddr & tcp port")

        for _ in range(60):
            machine = api.cloudapi.machines.get(machineId=machine_id)
            if j.data.types.ipaddress.check(machine['interfaces'][0]['ipAddress']):
                break
            else:
                time.sleep(1)
        if not j.data.types.ipaddress.check(machine['interfaces'][0]['ipAddress']):
            raise j.exceptions.RuntimeError('E:Machine was created, but never got an IP address')

        self.vars["machine.ip.addr"] = machine['interfaces'][0]['ipAddress']

        # push initial key
        self.sendUserMessage("push initial ssh key")
        self._getSSHConnection(spacesecret, name, sshkey=sshkey, **args)

        self.sendUserMessage("machine active & reachable")

        self.sendUserMessage("to connect from outise cloudspace do: 'ssh %s -p %s'" % (self.vars["space.ip.pub"], self.vars["machine.last.tcp.port"]))
        self.sendUserMessage("to connect from inside cloudspace do: 'ssh %s -p %s'" % (self.vars["machine.ip.addr"], 22))

        return machine_id, self.vars["space.ip.pub"], (int(self.vars["machine.last.tcp.port"]) if self.vars["machine.last.tcp.port"] else 22)

    def getMachineObject(self,spacesecret, name,**args):
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        machine = api.cloudapi.machines.get(machineId=machine_id)
        return machine

    def listImages(self,spacesecret,**args):

        if self.db.exists("ms1", "ms1:cache:%s:images"%spacesecret):
            return j.data.serializer.json.loads(self.db.get('ms1', "ms1:cache:%s:images"%spacesecret))

        api = self.getApiConnection(spacesecret)
        result={}
        imagetypes=["ubuntu.jumpscale","fedora","windows","ubuntu.13.10","ubuntu.12.04","windows.essentials","ubuntu.14.04.x64","ubuntu 14.04 x64",\
            "zentyal","debian.7","arch","fedora","centos","opensuse","gitlab"]
        for image in api.cloudapi.images.list():
            name=image["name"]
            namelower=name.lower()
            for imagetype in imagetypes:
                if namelower.find(imagetype) != -1:
                    result[imagetype]=[image["id"],image["name"], image['size']]
            result[image['name']]=[image["id"],image["name"], image['size']]

        self.db.set("ms1", "ms1:cache:%s:images"%spacesecret,j.data.serializer.json.dumps(result))
        return result

    def listMachinesInSpace(self, spacesecret,**args):
        # get actors
        api = self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        # list machines
        machines = api.cloudapi.machines.list(cloudspaceId=cloudspace_id)
        return machines

    def _getMachineApiActorId(self, spacesecret, name,**args):
        api=self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        machine_id = [machine['id'] for machine in api.cloudapi.machines.list(cloudspaceId=cloudspace_id) if machine['name'] == name]
        if len(machine_id)==0:
            raise j.exceptions.RuntimeError("E:Could not find machine with name:%s, cannot continue action."%name)
        machine_id = machine_id[0]
        return (api, machine_id, cloudspace_id)

    def deleteMachine(self, spacesecret, name,**args):
        self.sendUserMessage("delete machine: %s"%(name))
        try:
            api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        except Exception as e:
            if str(e).find("Could not find machine")!=-1:
                return "NOTEXIST"
            if str(e).find("Space secret does not exist")!=-1:
                return "E:SPACE SECRET IS NOT CORRECT"
            raise j.exceptions.RuntimeError(e)
        try:
            api.cloudapi.machines.delete(machineId=machine_id)
        except Exception as e:
            print(e)
            raise j.exceptions.RuntimeError("E:could not delete machine %s"%name)
        return "OK"

    def startMachine(self, spacesecret, name,**args):
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        try:
            api.cloudapi.machines.start(machineId=machine_id)
        except Exception as e:
            raise j.exceptions.RuntimeError("E:could not start machine.")
        return "OK"

    def stopMachine(self, spacesecret, name,**args):
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        try:
            api.cloudapi.machines.stop(machineId=machine_id)
        except Exception as e:
            raise j.exceptions.RuntimeError("E:could not stop machine.")
        return "OK"

    def snapshotMachine(self, spacesecret, name, snapshotname,**args):
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        try:
            api.cloudapi.machines.snapshot(machineId=machine_id, name=snapshotname)
        except Exception as e:
            raise j.exceptions.RuntimeError("E:could not stop machine.")
        return "OK"

    def createTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip="", pubipport=22,**args):
        self.vars["machine.last.tcp.port"]=pubipport
        return self._createPortForwardRule(spacesecret, name, machinetcpport, pubip, pubipport, 'tcp')

    def createUdpPortForwardRule(self, spacesecret, name, machineudpport, pubip="", pubipport=22,**args):
        return self._createPortForwardRule(spacesecret, name, machineudpport, pubip, pubipport, 'udp')

    def deleteTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip='', pubipport=22,**args):
        return self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'tcp')

    def deleteUdpPortForwardRule(self, spacesecret, name, machinetcpport, pubip='', pubipport=22,**args):
        return self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'udp')

    def _createPortForwardRule(self, spacesecret, name, machineport, pubip, pubipport, protocol):
        # self.sendUserMessage("Create PFW rule:%s %s %s"%(pubip,pubipport,protocol),args=args)
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        if pubip=="":
            cloudspace = api.cloudapi.cloudspaces.get(cloudspaceId=cloudspace_id)
            pubip=cloudspace['publicipaddress']

        self.vars["space.ip.pub"]=pubip
        self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'tcp')
        api.cloudapi.portforwarding.create(cloudspaceid=cloudspace_id, publicIp=pubip,
                                           publicPort=str(pubipport), vmid=machine_id,
                                           localPort=str(machineport), protocol=protocol)

        return "OK"

    def addDisk(self, spaceSecret, vmName, diskName, size=10, description=None, type='D'):
        """
        Add a disk to a vm
        @param spaceSecret str: cloudspace secret
        @param vmName str: name of the vm
        @param diskName str: name of the disk
        @param size int: size of the disk in GB, min 1, max 2000
        @param description str: description of the disk
        @param type str: type of the disk B=Boot;D=Data;T=Temp
        """
        types = ['B', 'D', 'T']
        if type not in types:
            raise j.exceptions.Input('type should be one of these : %s' ', '.join(types))

        if int(size) > 2000:
            raise j.exceptions.Input('max size is 2000 GB')
        if int(size) < 1:
            raise j.exceptions.Input('min size is 1 GB')

        api, machine_id, cloudspace_id = self._getMachineApiActorId(spaceSecret, vmName)

        vmStatus = api.cloudapi.machines.get(machineId=machine_id)
        if vmStatus['status'] != 'HALTED':
            j.events.opserror_critical('The VM should be alted to add a disk', category='')

        self.sendUserMessage('creation of the disk %s (%s GB)' % (diskName, size))
        api.cloudapi.machines.addDisk(machineId=machine_id, diskName=diskName, description=description,
                                      size=size, type=type)

    def _deletePortForwardRule(self, spacesecret, name,pubip,pubipport, protocol):
        # self.sendUserMessage("Delete PFW rule:%s %s %s"%(pubip,pubipport,protocol),args=args)
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)
        if pubip=="":
            cloudspace = api.cloudapi.cloudspaces.get(cloudspaceId=cloudspace_id)
            pubip=cloudspace['publicipaddress']

        for item in api.cloudapi.portforwarding.list(cloudspaceid=cloudspace_id):
            if int(item["publicPort"])==int(pubipport) and item['publicIp']==pubip:
                print(("delete portforward: %s "%item["id"]))
                api.cloudapi.portforwarding.delete(cloudspaceid=cloudspace_id, id=item["id"])

        return "OK"

    def getFreeIpPort(self,spacesecret,mmin=90,mmax=1000,**args):
        api=self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)

        space = api.cloudapi.cloudspaces.get(cloudspaceId=cloudspace_id)

        self.vars["space.free.tcp.addr"]=space["publicipaddress"]
        self.vars["space.ip.pub"]=space["publicipaddress"]

        pubip=space["publicipaddress"]

        tcpports={}
        udpports={}
        for item in api.cloudapi.portforwarding.list(cloudspaceid=cloudspace_id):
            if item['publicIp']==pubip:
                if item['protocol']=="tcp":
                    tcpports[int(item['publicPort'])]=True
                elif item['protocol']=="udp":
                    udpports[int(item['publicPort'])]=True

        for i in range(mmin,mmax):
            if i not in tcpports and i not in udpports:
                break

        if i>mmax-1:
            raise j.exceptions.RuntimeError("E:cannot find free tcp or udp port.")


        self.vars["space.free.tcp.port"]=str(i)
        self.vars["space.free.udp.port"]=str(i)

        return self.vars

    def listPortforwarding(self,spacesecret, name,**args):
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)

        machine = api.cloudapi.machines.get(machineId=machine_id)
        if machine['cloudspaceid'] != cloudspace_id:
            return 'Machine %s does not belong to cloudspace whose secret is given' % name

        items = api.cloudapi.portforwarding.list(cloudspaceid=cloudspace_id)

        if len(machine["interfaces"])>0:
            local_ipaddr=machine["interfaces"][0]['ipAddress'].strip()
        else:
            raise j.exceptions.RuntimeError("cannot find local ip addr")

        items=[]
        for item in api.cloudapi.portforwarding.list(cloudspaceid=cloudspace_id):
            if item['localIp']==local_ipaddr:
                items.append(item)
        return items

    def _getSSHConnection(self, spacesecret, name, sshkey=None, **args):
        api, machine_id, cloudspace_id = self._getMachineApiActorId(spacesecret, name)

        machine = api.cloudapi.machines.get(machineId=machine_id)
        if machine['cloudspaceid'] != cloudspace_id:
            return 'Machine %s does not belong to cloudspace whose secret is given' % name


        print("RECREATE SSH CONNECTION")
        items=api.cloudapi.portforwarding.list(cloudspaceid=cloudspace_id)

        if len(machine["interfaces"])>0:
            local_ipaddr=machine["interfaces"][0]['ipAddress'].strip()
        else:
            raise j.exceptions.RuntimeError("cannot find local ip addr")

        #remove leftovers
        for item in items:
            if item['localIp'].strip()==local_ipaddr and int(item['localPort'])==22:
                self.sendUserMessage("Delete existing PFW rule:%s %s"%(item['localIp'],22),args=args)
                try:
                    api.cloudapi.portforwarding.delete(cloudspaceid=cloudspace_id, id=item["id"])
                except Exception as e:
                    self.sendUserMessage("Warning: could not delete.",args=args)

        tempportdict=self.getFreeIpPort(spacesecret,mmin=1500,mmax=1999,**args)
        tempport=tempportdict['space.free.tcp.port']

        counter=1
        localIP=machine["interfaces"][0]["ipAddress"]
        while localIP=="" or localIP.lower()=="undefined":
            print("NO IP YET")
            machine = api.cloudapi.machines.get(machineId=machine_id)
            counter+=1
            time.sleep(0.5)
            if counter>100:
                raise j.exceptions.RuntimeError("E:could not find ip address for machine:%s"%name)
            localIP=machine["interfaces"][0]["ipAddress"]

        self.createTcpPortForwardRule(spacesecret, name, 22, pubipport=tempport,**args)

        cloudspace = api.cloudapi.cloudspaces.get(cloudspaceId=cloudspace_id)
        pubip=cloudspace['publicipaddress']

        connectionAddr = cloudspace['publicipaddress']
        connectionPort = tempport
        counter = 0
        while counter < 3:
            if not j.sal.nettools.waitConnectionTest(cloudspace['publicipaddress'], int(tempport), 5):
                # if we can't connect with public IP, it probably means we try to access the vm from inside the cloudspace with another vm
                # so we try to connect using the private ip
                if not j.sal.nettools.waitConnectionTest(local_ipaddr, 22, 5):
                    if counter >=3:
                        # if still can't connect, then it's an error
                        raise j.exceptions.RuntimeError("E:Failed to connect to %s" % (tempport))
                else:
                    connectionAddr = local_ipaddr
                    connectionPort = 22
                    break
                counter = counter+1
            else:
                break

        # if we don't specify the key to push
        # create one first
        key = None
        if sshkey is None:
            keyloc = "/root/.ssh/id_rsa.pub"

            if not j.sal.fs.exists(path=keyloc):
                j.sal.process.executeWithoutPipe("ssh-keygen -t rsa")
                if not j.sal.fs.exists(path=keyloc):
                    raise j.exceptions.RuntimeError("cannot find path for key %s, was keygen well executed"%keyloc)

            j.sal.fs.chmod("/root/.ssh/id_rsa", 0o600)
            key = j.sal.fs.fileGetContents(keyloc)
        else:
            key = sshkey

        rloc = "/root/.ssh/authorized_keys"

        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']

        executor = j.tools.executor.getSSHBased(addr=connectionAddr, port=connectionPort, login=username, passwd=password)
        ssh_connection = j.tools.cuisine.get(executor)

        name = name.replace('_', '').replace(' ', '-')
        ssh_connection.sudomode = True
        ssh_connection.run('echo %s > /etc/hostname' % name, warn_only=True)
        ssh_connection.run('hostname %s' % name, warn_only=True)
        ssh_connection.run('echo "127.0.0.1 %s" >> /etc/hosts' % name, warn_only=True)

        # will overwrite all old keys
        ssh_connection.file_write(rloc, key)

        return ssh_connection

    def execSshScript(self, spacesecret, name,**args):

        ssh_connection=self._getSSHConnection(spacesecret,name,**args)

        if "lines" in args:
            script=args["lines"]
            out=""
            for line in script.split("\n"):
                line=line.strip()
                if line.strip()=="":
                    continue
                if line[0]=="#":
                    continue
                out+="%s\n"%line
                print(line)

                result= ssh_connection.run(line+"\n")
                out+="%s\n"%result
                print(result)

        elif "script" in args:
            script=args["script"]
            script="set +ex\n%s"%script
            print("SSHPREPARE:")
            print(script)
            ssh_connection.file_write("/tmp/do.sh",script)
            ssh_connection.fabric.context_managers.show("output")

            from io import StringIO
            import sys

            sys.stdout=self.stdout

            # ssh_connection.run("sh /tmp/do.sh", pty=False, combine_stderr=True,stdout=fh)
            try:
                out=ssh_connection.run("sh /tmp/do.sh",combine_stderr=True)
            except BaseException as e:
                sys.stdout=self.stdout.prevout
                if self.stdout.lastlines.strip()!="":
                    msg="Could not execute sshscript:\n%s\nError:%s\n"%(script,self.stdout.lastlines)
                    self.action.raiseError(msg)
                    self.stdout.lastlines=""
                print(e)
                raise j.exceptions.RuntimeError("E:Could not execute sshscript, errors.")
            sys.stdout=self.stdout.prevout

        else:
            raise j.exceptions.RuntimeError("E:Could not find param script or lines")


        return out
