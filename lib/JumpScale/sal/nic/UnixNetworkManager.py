from JumpScale import j
#
import re
import netaddr

# class NetworkingErro(Exception):
#     pass


class NetworkingError(Exception):
    pass




class UnixNetworkManager:

    def __init__(self):
        self.__jslocation__ = "j.sal.nic"
        self.logger = j.logger.get("j.sal.nic")
        self._executor = j.tools.executor.getLocal()
        self._nics = None

    def _nicExists(self, nic):
        if nic not in self.nics:
            raise NetworkingError('Invalid NIC')

    def ipGet(self, device):
        """
        Get IP of devie
        Result (ip, netmask, gateway)
        """
        self._nicExists(device)
        cmd  = 'echo `ip a | grep %s | sed -n 2p | xargs | cut -d " " -f 2`' % device
        rc, res = self._executor.execute(cmd)
        ipmask = netaddr.IPNetwork(res)
        netmask = str(ipmask.netmask)
        ip = str(ipmask.ip)
        return (ip, netmask)

    def ipSet(self, device, ip=None, netmask=None, gw=None, inet='dhcp', commit=False):
        """
        Return all interfaces that has this ifname
        """
        self._nicExists(device)

        if inet not in ['static', 'dhcp']:
            raise ValueError('Invalid inet .. use either dhcp or static')

        if inet == 'static' and (not ip or not netmask):
            raise ValueError('ip, and netmask, are required in static inet.')

        file = j.tools.path.get('/etc/network/interfaces.d/%s' % device)
        content = 'auto %s\n' % device

        if inet == 'dhcp':
            content += 'iface %s inet dhcp\n' % device
        else:
            content += 'iface %s inet static\naddress %s\nnetmask %s\n' % (device, ip, netmask)
            if gw:
                content += 'gateway %s\n' % gw

        file.write_text(content)

        if commit:
            self.commit(device)
        else:
            self.logger.info('Do NOT FORGET TO COMMIT')

    def ipReset(self, device, commit=False):
        self._nicExists(device)
        file = j.tools.path.get('/etc/network/interfaces.d/%s' % device)
        file.write_text('')

        if commit:
            self.commit()
        else:
            self.logger.info('Do NOT FORGET TO COMMIT')

    @property
    def nics(self):
        if self._nics is None:
            rc, ifaces =  self._executor.execute('ls --color=never -1 /sys/class/net')
            self._nics = [iface for iface in ifaces.splitlines() if iface]
        return self._nics



    def commit(self, device=None):
        #- make sure loopback exist
        content = 'auto lo\niface lo inet loopback\n'
        j.tools.path.get('/etc/network/interfaces.d/lo').write_text(content)

        self._executor.execute('service networking restart')
        if device:
            self.logger.info('Restarting interface %s' % device)
            self._executor.execute('ifdown %s && ifup %s' % (device, device))
        self.logger.info('DONE')
