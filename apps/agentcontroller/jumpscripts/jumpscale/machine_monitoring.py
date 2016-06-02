from JumpScale import j

descr = """
gather statistics about machines
"""

organization = "jumpscale"
author = "deboeckj@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitoring.machine"
period = 60*60 #always in sec
timeout = period * 0.2
order = 1
enable=True
async=True
queue='process'
log=False

roles = []

from xml.etree import ElementTree
try:
    import libvirt
except:
    enable=False

def getContentKey(obj):
    dd=j.code.object2json(obj, True, ignoreKeys=["guid","id","sguid","moddate", 'lastcheck'], ignoreUnderscoreKeys=True)
    return j.data.hash.md5_string(str(dd))

def action():
    syscl = j.data.models.system
    con = libvirt.open('qemu:///system')
    #con = libvirt.open('qemu+ssh://10.101.190.24/system')
    stateMap = {libvirt.VIR_DOMAIN_RUNNING: 'RUNNING',
                libvirt.VIR_DOMAIN_NOSTATE: 'NOSTATE',
                libvirt.VIR_DOMAIN_PAUSED: 'PAUSED'}

    allmachines = syscl.Machine.find({'nid': j.application.whoAmI.nid,
                                        'gid': j.application.whoAmI.gid, 
                                        'state': {'$ne': 'DELETED'}
                                        })
    allmachines = {machine['guid']: machine for machine in allmachines }
    domainmachines = list()
    try:
        domains = con.listAllDomains()
        for domain in domains:
            try:
                machine = syscl.Machine()
                machine.id = domain.ID()
                machine.guid = domain.UUIDString().replace('-', '')
                domainmachines.append(machine.guid)
                machine.name = domain.name()
                print ('Processing', machine.name)
                machine.nid = j.application.whoAmI.nid
                machine.gid = j.application.whoAmI.gid
                machine.type = 'KVM'
                xml = ElementTree.fromstring(domain.XMLDesc())
            except:
                continue  # machine was destroyed during inspection
            netaddr = dict()
            for interface in xml.findall('devices/interface'):
                mac = interface.find('mac').attrib['address']
                alias = interface.find('alias')
                name = None
                if alias is not None:
                    name = alias.attrib['name']
                netaddr[mac] = [ name, None ]


            machine.mem = int(xml.find('memory').text)
            machine.netaddr = netaddr
            machine.lastcheck = j.data.time.getTimeEpoch()
            machine.state = stateMap.get(domain.state()[0], 'STOPPED')
            machine.cpucore = int(xml.find('vcpu').text)

            old = syscl.Machine.find({'guid':machine.guid})
            if old:
                old_machine = old[0].to_dict()
                for key in ['mem', 'netaddr', 'lastcheck', 'state', 'cpucore']:
                    if old_machine[key] != machine[key]:
                        old[0].delete()
                        print ('Saving', machine.name)
                        machine.save()
                        break


            for disk in xml.findall('devices/disk'):
                if disk.attrib['device'] != 'disk':
                    continue
                diskattrib = disk.find('source').attrib
                path = diskattrib.get('dev', diskattrib.get('file'))
                vdisk = syscl.VDisk()
                old = syscl.VDisk.find({'path':path})
                vdisk.path = path
                vdisk.type = disk.find('driver').attrib['type']
                vdisk.devicename = disk.find('target').attrib['dev']
                vdisk.machineid = machine.guid
                vdisk.active = j.sal.fs.exists(path)
                if vdisk.active:
                    try:
                        diskinfo = j.sal.qemu_img.info(path)
                        vdisk.size = diskinfo['virtual size']
                        vdisk.sizeondisk = diskinfo['disk size']
                        vdisk.backingpath = diskinfo.get('backing file', '')
                    except Exception:
                        # failed to get disk information
                        vdisk.size = -1
                        vdisk.sizeondisk = -1
                        vdisk.backingpath = ''
                if old:
                   old_disk = old[0].to_dict()
                   for key in ['path', 'type', 'devicename', 'machineid', 'active', 'size', 'sizeondisk', 'backingpath']:
                       if old_disk[key] != vdisk[key]:
                           old[0].delete()
                           vdisk.save()
                           break


    finally:
        deletedmachines = set(allmachines.keys()) - set(domainmachines)
        for deletedmachine in deletedmachines:
            machine = allmachines[deletedmachine]
            print ('Deleting', machine['name'])
            machine['state'] = 'DELETED'
            machine.delete()
        con.close()

if __name__ == '__main__':
    action()
