from os import remove
from shutil import copy
import random
import socket
import struct
from nose.tools import assert_equal

from JumpScale import j

def generate_rnd_ip():
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff))) #generate random ip

class TestHostFile:

    def setUp(self):
        copy("/etc/hosts", "/tmp/hosts_testfile")
        self.hostsfile = j.sal.hostsfile.get()
        self.hostsfile.hostfilePath = "/tmp/hosts_testfile"

    def tearDown(self):
        remove("/tmp/hosts_testfile")

    def test_remove(self):
        ip = generate_rnd_ip()
        domains = ["remove.test", "remove2.test"]

        self.hostsfile.set(ip, domains)
        assert_equal(self.hostsfile.existsIP(ip), True)
        self.hostsfile.remove(ip)
        assert_equal(self.hostsfile.existsIP(ip), False)

    def test_existsIP(self):
        ip = generate_rnd_ip()
        not_exists_ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
        domains = ["exists.test", "exists2.test"]
        self.hostsfile.set(ip, domains)
        assert_equal(True, self.hostsfile.existsIP(ip))
        assert_equal(False, self.hostsfile.existsIP(not_exists_ip))
        self.hostsfile.remove(ip)

    def test_remove_ip_doesnt_exist(self):
        #does nothing..
        unrealip="8911.124.12.41111"
        oldcontent, newcontent= "", ""
        with open("/tmp/hosts_testfile") as f:
            oldcontent = f.read()
            assert_equal(unrealip in oldcontent, False)
        self.hostsfile.remove(unrealip)

        with open("/tmp/hosts_testfile") as f:
            newcontent = f.read()
            assert_equal(oldcontent, newcontent)

    def test_getNames(self):
        ip = generate_rnd_ip()
        domains = ["test_domain", "test_domain2"]
        self.hostsfile.set(ip, domains)
        names = self.hostsfile.getNames(ip)
        assert_equal(names, domains)
        self.hostsfile.remove(ip)

    def test_set(self):
        ip = generate_rnd_ip()
        domains = ["test_set.com", "test_set2.com"]
        self.hostsfile.set(ip, domains)
        assert_equal(self.hostsfile.existsIP(ip), True)
        self.hostsfile.remove(ip)