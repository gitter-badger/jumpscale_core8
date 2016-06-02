from libcloud.compute.providers import get_driver
from JumpScale import j



class AmazonProvider:

    def __init__(self):
        self._region = None
        self._client = None

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        self._region = 'ec2_%s' % value

    def connect(self, access_key_id, secret_access_key):
        if not self.region:
            raise j.exceptions.RuntimeError('Region must be set first')
        self._client = get_driver(self.region)(access_key_id, secret_access_key)

    def find_size(self, size_id):
        return [s for s in self._client.list_sizes(self.region) if s.id.lower().find(size_id.lower()) != -1]

    def find_image(self, image_id):
        return [i for i in self._client.list_images(self.region) if i.id.lower().find(image_id.lower()) != -1]

    def list_machines(self):
        result = list()
        machines = self._client.list_nodes()
        for machine in machines:
            data = dict()
            data['id'] = machine.id
            data['name'] = machine.name
            data['public_ips'] = machine.public_ips
            data['private_ips'] = machine.private_ips
            data['image_id'] = machine.extra.get('image_id', None)
            data['status'] = machine.extra.get('status', None)
            data['size_id'] = machine.extra.get('instance_type', None)
            result.append(data)
        return result

    def create_machine(self, name, image, size, ssh_key_name, ssh_key_file):
        self.import_keypair(ssh_key_name, ssh_key_file)
        return self._client.create_node(name=name, image=image, size=size, ex_keyname=ssh_key_name)

    def execute_command(self, machine_name, command, sudo=False):
        machines = self.list_machines()
        host = None
        for machine in machines:
            if machine['name'] == machine_name:
                if machine['status'] != 'running':
                    raise j.exceptions.RuntimeError('Machine "%s" is not running' % machine_name)
                host = machine['public_ips'][0]
                break

        if not host:
            raise j.exceptions.RuntimeError('Could not find machine: %s' % machine_name)
        rapi = j.tools.cuisine.get(j.tools.executor.get(host, login='ubuntu'))
        if sudo:
            return rapi.core.sudo(command)
        return rapi.core.run(command)

    def import_keypair(self, name, key_file):
        self._client.ex_import_keypair(name, key_file)