#!/usr/bin/env python
from JumpScale import j
from libvirtutil import LibvirtUtil


"""
HRDIMAGE format
id=
name=
ostype =
arch=
version=
description=
pub.ip=
bootstrap.ip=
bootstrap.login=
bootstrap.passwd=
bootstrap.type=ssh
fabric.module=
shell=
root.partitionnr=
"""


from sal.base.SALObject import SALObject

class KVM(SALObject):

    def __init__(self):
        """
        each vm becomes a subdir underneath the self.vmpath
        relevant info (which we need to remember, so which cannot be fetched from reality through libvirt) is stored in $vmpath/$name/vm.$name.hrd

        for networking in this first release we put 3 nics attached to std bridges
        - names of bridges are brmgmt & brpub & brtmp(and are predefined)
        - brpub will be connected to e.g. eth0 on host and is for public traffic
        - brtmp is not connected to any physical device
        - brmgmt is not connected to physical device, it is being used for mgmt of vm

        images are always 2 files:
         $anyname.qcow2
         $anyname.hrd

        the hrd has all info relevant to vm (see HRDIMAGE constant)

        ostype is routeros,openwrt,ubuntu,windows, ...
        architecture i386,i64
        version e.g. 14.04
        name e.g. ourbase

        each image needs to have ssh agent installed and needs to be booted when machine starts & be configured using the params as specified
        """
        self.__jslocation__ = "j.sal.kvm"
        self.vmpath = "/mnt/vmstor/kvm"
        self.imagepath = "/mnt/vmstor/kvm/images"
        self.images = {}
        self.loadImages()
        self.LibvirtUtil = LibvirtUtil()
        self.LibvirtUtil.basepath = self.vmpath

    def _getRootPath(self, name):
        return j.sal.fs.joinPaths(self.vmpath, name)

    def loadImages(self):
        """
        walk over images & remember so we can use to create & manipulate machines
        """
        for image in j.sal.fs.listDirsInDir(self.imagepath, recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
            path = j.sal.fs.joinPaths(self.imagepath, image, '%s.hrd' % image)
            hrd = j.data.hrd.get(path)
            self.images[image] = hrd

    def list(self):
        """
        names of running & stopped machines
        @return (running,stopped)
        """
        machines = self.LibvirtUtil.list_domains()
        running = [machine for machine in machines if machine['state'] == 1]
        stopped = [machine for machine in machines if machine['state'] == 5 and j.sal.fs.exists(j.sal.fs.joinPaths(self.vmpath, machine['name']))]
        return (running, stopped)

    def listSnapshots(self, name):
        machine_hrd = self.getConfig(name)
        return [s['name'] for s in self.LibvirtUtil.listSnapshots(machine_hrd.get('name'))]

    def getIp(self, name):
        #info will be fetched from hrd in vm directory
        machine_hrd = self.getConfig(name)
        if machine_hrd:
            return machine_hrd.get("bootstrap.ip")

    def getConfig(self, name):
        configpath = j.sal.fs.joinPaths(self.vmpath, name, "main.hrd")
        if not j.sal.fs.exists(path=configpath):
            print('Machine %s does not exist' % name)
            return
        return j.data.hrd.get(path=configpath)

    def _getAllMachinesIps(self):
        """
        walk over all vm's, get config & read ip addr
        put them in dict
        """
        ips = dict()
        for name in self._getAllVMs():
            hrd = self.getConfig(name)
            if hrd:
                ips[name] = hrd.get("bootstrap.ip"), hrd.get("pub.ip")
        return ips

    def _getAllVMs(self):
        result = j.sal.fs.listDirsInDir(self.vmpath, recursive=False, dirNameOnly=True, findDirectorySymlinks=True)
        result.remove('images')
        return result

    def _findFreeIP(self, name):
        return self._findFreePubIP(name)

    def _findFreePubIP(self, name, pub=False):
        """
        find first ip addr which is free
        """
        ips=self._getAllMachinesIps()
        addr=[]
        for key,ip in list(ips.items()):
            if pub:
                addr.append(int(ip[1].split(".")[-1].strip()))
            else:
                addr.append(int(ip[0].split(".")[-1].strip()))

        for i in range(2,252):
            if i not in addr:
                if pub:
                    return '10.0.0.%s' % i
                else:
                    return '192.168.66.%s' % i

        raise j.exceptions.OPERATIONS("could not find free ip addr for KVM in 192.168.66.0/24 range","kvm.ipaddr.find")


    def create(self, name, baseimage, replace=True, description='', size=10, memory=512, cpu_count=1, bridges=None):
        """
        create a KVM machine which inherits from a qcow2 image (so no COPY)

        always create a 2nd & 3e & 4th disk
        all on qcow2 format
        naming convention
        $vmpath/$name/tmp.qcow2
            $vmpath/$name/data1.qcow2
            $vmpath/$name/data2.qcow2
        one is for all data other is for tmp

        when attaching to KVM: disk0=bootdisk, disk1=tmpdisk, disk2=datadisk1, disk3=datadisk2

        eth0 attached to brmgmt = for mgmt purposes
        eth1 to brpub
        eth2 to brtmp
        each machine gets an IP address from brmgmt range on eth0
        eth1 is attached to pubbridge
        eth2 is not connected to anything

        @param baseimage is name of the image used (see self.images)

        @param size disk size in GBs
        @param memory memory size in MBs
        @param cpu_count is the number of vCPUs

        when replace then remove original image
        """
        bridges = bridges or []
        if replace:
            if j.sal.fs.exists(self._getRootPath(name)):
                print('Machine %s already exists, will destroy and recreate...' % name)
                self.destroy(name)
                j.sal.fs.removeDirTree(self._getRootPath(name))
        else:
            if j.sal.fs.exists(self._getRootPath(name)):
                print('Error creating machine "%s"' % name)
                raise j.exceptions.RuntimeError('Machine "%s" already exists, please explicitly specify replace=True(default) if you want to create a vmachine with the same name' % name)
        j.sal.fs.createDir(self._getRootPath(name))
        print('Creating machine %s...' % name)
        try:
            self.LibvirtUtil.create_node(name, baseimage, bridges=bridges, size=size, memory=memory, cpu_count=cpu_count)
        except Exception as e:
            print('Error creating machine "%s"' % name)
            print('Rolling back machine creation...')
            return self.destroy(name)
        print('Wrtiting machine HRD config file...')
        domain = self.LibvirtUtil.connection.lookupByName(name)
        imagehrd = self.images[baseimage]
        hrdfile = j.sal.fs.joinPaths(self._getRootPath(name), 'main.hrd')
        # assume that login and passwd are provided in the image hrd config file
        hrdcontents = '''id=%s
name=%s
image=%s
ostype=%s
arch=%s
version=%s
description=%s
root.partitionnr=%s
memory=%s
disk_size=%s
cpu_count=%s
shell=%s
fabric.module=%s
pub.ip=%s
bootstrap.ip=%s
bootstrap.login=%s
bootstrap.passwd=%s
bootstrap.type=ssh''' % (domain.UUIDString(), name, imagehrd.get('name'), imagehrd.get('ostype'), imagehrd.get('arch'), imagehrd.get('version'), description, imagehrd.get('root.partitionnr', '1'),
        memory, size, cpu_count, imagehrd.get('shell', ''), imagehrd.get('fabric.module'), imagehrd.get('pub.ip'), imagehrd.get('bootstrap.ip'), imagehrd.get('bootstrap.login'), imagehrd.get('bootstrap.passwd'))
        j.sal.fs.writeFile(hrdfile, hrdcontents)
        print('Machine %s created successfully' % name)

        mgmt_ip = self._findFreeIP(name)
        machine_hrd = self.getConfig(name)
        machine_hrd.set('bootstrap.ip', mgmt_ip)
        public_ip = self._findFreePubIP(name, True)
        machine_hrd.set('pub.ip', public_ip)

        print('Machine IP address is: %s' % mgmt_ip)
        return mgmt_ip

    def destroyAll(self):
        print('Destroying all created vmachines...')
        running, stopped = self.list()
        for item in running + stopped:
            self.destroy(item['name'])
        print('Done')

    def destroy(self, name):
        print('Destroying machine "%s"' % name)
        try:
            self.LibvirtUtil.delete_machine(name)
        except:
            pass
        finally:
            j.sal.fs.removeDirTree(self._getRootPath(name))

    def stop(self, name):
        print('Stopping machine "%s"' % name)
        try:
            self.LibvirtUtil.shutdown(name)
            print('Done')
        except:
            pass

    def start(self, name):
        print('Starting machine "%s"' % name)
        try:
            self.LibvirtUtil.create(name, None)
            print('Done')
        except:
            pass

    def pause(self, name):
        print('Pausing machine "%s"' % name)
        try:
            self.LibvirtUtil.suspend(name)
            print('Done')
        except:
            pass

    def resume(self, name):
        print('Resuming machine "%s"' % name)
        try:
            self.LibvirtUtil.resume(name)
            print('Done')
        except:
            pass



    def snapshot(self, name, snapshotname, disktype='all', snapshottype='external'):
        """
        take a snapshot of the disk(s)
        @param disktype = all,root,data1,data2
        #todo define naming convention for how snapshots are stored on disk
        """
        print('Creating snapshot %s for machine %s' % (snapshotname, name))
        machine_hrd = self.getConfig(name)
        try:
            self.LibvirtUtil.snapshot(machine_hrd.get('name'), snapshotname, snapshottype=snapshottype)
            print('Done')
        except:
            pass

    # def deleteSnapsho is not working properly .. has to do with libvirtutil itself .. todo
    def deleteSnapshot(self, name, snapshotname):
        '''
        deletes a vmachine snapshot
        @param name: vmachine name
        @param snapshotname: snapshot name
        '''
        machine_hrd = self.getConfig(name)
        print('Deleting snapshot %s for machine %s' % (snapshotname, name))
        if snapshotname not in self.listSnapshots(name):
            print("Couldn't find snapshot %s for machine %s" % (snapshotname, name))
            return
        self.LibvirtUtil.deleteSnapshot(name, snapshotname)

    def mountSnapshot(self, name, snapshotname, location='/mnt/1', dev='/dev/nbd1', partitionnr=None):
        """
        try to mount the snapshotted disk to a location
        at least supported btrfs,ext234,ntfs,fat,fat32
        """
        machine_hrd = self.getConfig(name)
        if not machine_hrd:
            raise j.exceptions.RuntimeError('Machine "%s" does not exist' % name)
        if snapshotname not in self.listSnapshots(name):
            raise j.exceptions.RuntimeError('Machine "%s" does not have a snapshot named "%s"' % (name, snapshotname))
        print(('Mounting snapshot "%s" of mahcine "%s" on "%s"' % (snapshotname, name, location)))
        if not j.sal.fs.exists(location):
            print(('Location "%s" does not exist, it will be created' % location))
            j.sal.fs.createDir(location)
        print(('Device %s will be used, freeing up first...' % dev))
        exitcode, modules = j.sal.process.execute('lsmod')
        if 'nbd' not in modules:
            j.sal.process.execute('modprobe nbd max_part=8')
        self._cleanNbdMount(location, dev)
        qcow2_images = j.sal.fs.listFilesInDir(j.sal.fs.joinPaths(self.vmpath, name), filter='*.qcow2')
        snapshot_path = None
        for qi in qcow2_images:
            if snapshotname in qi:
                snapshot_path = qi
                break
        if not snapshot_path:
            raise j.exceptions.RuntimeError('Could not find snapshot "%s" path' % snapshotname)
        j.sal.process.execute('qemu-nbd --connect=%s %s' % (dev, snapshot_path))
        if not partitionnr:
            partitionnr = machine_hrd.get('root.partitionnr', '1')
        j.sal.process.execute('mount %sp%s %s' % (dev, partitionnr, location))
        print(('Snapshot "%s" of mahcine "%s" was successfully mounted on "%s"' % (snapshotname, name, location)))

    def unmountSnapshot(self, location='/mnt/1', dev='/dev/nbd1'):
        self._cleanNbdMount(location, dev)

    def _cleanNbdMount(self, location, dev):
        print(('Unmounting location "%s"' % location))
        try:
            j.sal.process.execute('umount %s' % location)
        except:
            print(('location "%s" is already unmounted' % location))
        print(('Disconnecting dev "%s"' % dev))
        j.sal.process.execute('qemu-nbd -d %s' % dev)



