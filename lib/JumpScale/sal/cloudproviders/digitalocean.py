from libcloud.compute.providers import get_driver
from JumpScale import j

import time



class DigitalOcean:

    def __init__(self):
        self._client = None

    def connect(self, client_id, api_key):
        self._client = get_driver('digitalocean')(client_id, api_key)

    def find_size(self, size_name):
        return [s for s in self._client.list_sizes() if s.name.lower().find(size_name.lower()) != -1]

    def find_image(self, image_name):
        return [i for i in self._client.list_images() if i.name.lower().find(image_name.lower()) != -1 or i.extra['distribution'].lower().find(image_name.lower()) != -1]

    def find_location(self, location_name):
        return [l for l in self._client.list_locations() if l.name.lower().find(location_name.lower()) != -1]

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
            data['size_id'] = machine.extra.get('instance_type', None)
            result.append(data)
        return result

    def create_machine(self, name, image, size, location, ssh_key_name, ssh_key_file):
        self.import_keypair(ssh_key_name, ssh_key_file)
        time.sleep(5)
        return self._client.create_node(name=name, image=image, size=size, location=location, ex_ssh_key_ids=[ssh_key_name,])

    def execute_command(self, machine_name, command, sudo=False):
        machines = self.list_machines()
        host = None
        for machine in machines:
            if machine['name'] == machine_name:
                host = machine['public_ips'][0]
                break

        if not host:
            raise j.exceptions.RuntimeError('Could not find machine: %s' % machine_name)
        rapi = j.tools.cuisine.get(j.tools.executor.get(host))
        if sudo:
            return rapi.core.sudo(command)
        return rapi.core.run(command)

    def import_keypair(self, name, key_file):
        with open(key_file) as f:
            ssh_key = f.read()
        self._client.ex_create_ssh_key(name, ssh_key)