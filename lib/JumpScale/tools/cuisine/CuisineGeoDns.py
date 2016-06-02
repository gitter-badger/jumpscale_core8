from JumpScale import j
from ActionDecorator import ActionDecorator


class actionrun(ActionDecorator):

    def __init__(self, *args, **kwargs):
        ActionDecorator.__init__(self, *args, **kwargs)
        self.selfobjCode = "cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.geodns"


class Domain:

    def __init__(self, name, cuisine, serial=None,  ttl=None, content="", max_hosts=2,  a_records={}, cname_records={}, ns=[]):
        """
        @name = full domain name to be created or to edit
        @content = string with json of entire zone file to replace or create zonefile
        @a_records = dict of a_records and their subdomains
        @cname_records = list of c_records and thier subdomains
        @ttl = time to live specified if predefined in content will be replaced
        @serial = used as a uniques key
        @ns = list of name servers
        """
        self.cuisine = cuisine
        self.name = name
        if content:
            self.content = j.data.serializer.json.loads(content)
            if "ttl" in self.content:
                self.ttl = self.content["ttl"]
            if "max_hosts" in self.content:
                self.max_hosts = self.content["max_hosts"]
            if "serial" in self.content:
                self.serial = self.content["serial"]

            records_a = dict()
            for key, val in self.content["data"].items():
                if "a" in val:
                    records_a[key] = val["a"]
            self._a_records = records_a

            records_cname = dict()
            for key, val in self.content["data"].items():
                if "cname" in val:
                    records_cname[key] = val["cname"]
            self._cname_records = records_cname

            if "ns" in self.content["data"][""]:
                self.ns = self.content["data"][""]["ns"]

        else:
            self.content = {"data": {"": {}}}
            self._a_records = a_records
            self.name = name
            self.max_hosts = max_hosts
            self._cname_records = cname_records
            self.ttl = ttl
            self.serial = serial
            ns.append(name)
            self.ns = ns

    def add_subdomain(self, subdomain):
        if subdomain in self.content["data"]:
            return
        self.content["data"][subdomain] = {}

    def add_a_record(self, ip, subdomain="", weight=100):
        record = [ip, weight]
        if subdomain in self._a_records:
            for i, val in enumerate(self._a_records[subdomain]):
                    if ip == val[0]:
                        self._a_records[subdomain][i] = record
                        return
            else:
                return self._a_records[subdomain].append(record)

        self._a_records[subdomain] = [record]
        return self._a_records[subdomain]

    def get_a_record(self, subdomain=None):
        if subdomain is not None and subdomain in self._a_records:
            return self._a_records[subdomain]
        return self._a_records

    def del_a_record(self, subdomain, ip=None, full=True):
        if not ip and not full:
            raise Exception("cannot delete specific ip if not given")
        if full:
            return self._a_records.pop(subdomain)
        for i, val in enumerate(self._a_records[subdomain]):
                if ip == val[0]:
                    return self._a_records[subdomain].pop(i)

    def add_cname_record(self, value, subdomain=""):
        self._cname_records[subdomain] = value

    def get_cname_record(self, subdomain=None):
        if subdomain is not None and subdomain in self._cname_records:
            return self._cname_records[subdomain]
        return self._cname_records

    def del_cname_record(self, subdomain):
        return self._cname_records.pop(subdomain)

    def save(self):
        self.content = {"data": {"": {}}}
        for key, val in self._a_records.items():
            self.add_subdomain(key)
            self.content["data"][key]["a"] = val
        for key, val in self._cname_records.items():
            self.add_subdomain(key)
            self.content["data"][key]["cname"] = val

        self.content["ttl"] = self.ttl
        self.content["serial"] = self.serial
        self.content["max_hosts"] = self.max_hosts
        self.content["data"][""]["ns"] = self.ns
        config = j.data.serializer.json.dumps(self.content)
        self.cuisine.core.file_write("$cfgDir/geodns/dns/%s.json" % self.name, config)
        return config


class CuisineGeoDns:

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine

    @actionrun(action=True)
    def install(self):
        """
        installs and builds geodns from github.com/abh/geodns
        """
        # deps
        self.cuisine.golang.install()
        self.cuisine.package.install("libgeoip-dev")

        # build
        self.cuisine.golang.get("github.com/abh/geodns")

        # moving files and creating config
        self.cuisine.core.file_copy("$goDir/bin/geodns", "$binDir")
        self.cuisine.core.dir_ensure("$tmplsDir/cfg/geodns/dns", recursive=True)
        self.cuisine.bash.addPath('$binDir')

        self.cuisine.core.file_copy(
            "$tmplsDir/cfg/geodns", "$cfgDir/", recursive=True)

    def start(self, ip="0.0.0.0", port="5053", config_dir="$cfgDir/geodns/dns/", identifier="geodns_main", cpus="1", tmux=False):
        """
        starts geodns server with given params
        """
        if self.cuisine.core.dir_exists(config_dir):
            self.cuisine.core.dir_ensure(config_dir)
        cmd = "$binDir/geodns -interface %s -port %s -config=%s -identifier=%s -cpus=%s" % (ip, str(port), config_dir, identifier, str(cpus))
        if tmux:
            pm = self.cuisine.processmanager.get("tmux")
            pm.ensure(name=identifier, cmd=cmd, env={}, path="$binDir")
        else:
            self.cuisine.processmanager.ensure(name=identifier, cmd=cmd, env={}, path="$binDir")

    def stop(self, name="geodns_main"):
        """
        stop geodns server with @name
        """
        self.cuisine.processmanager.stop(name)

    @property
    def domains(self):
        domains = []
        for path in self.cuisine.core.fs_find('$cfgDir/geodns/dns/',type='f', pattern='*.json', recursive=False):
            basename = j.sal.fs.getBaseName(path)
            domains.append(basename.rstrip('.json'))
        return domains

    def ensure_domain(self, domain_name, serial=None,  ttl=None, content=None, max_hosts=2,  a_records={}, cname_records={}, ns=[]):
        """
        used to create a domain_name in dns server also updates if already exists
        @name = full domain name to be created or to edit
        @content = string with json of entire zone file to replace or create zonefile
        @a_records = dict of a_records and their subdomains
        @cname_records = list of c_records and thier subdomains
        @ttl = time to live specified if predefined in content will be replaced
        @serial = used as a uniques key
        @ns = list of name servers
        """
        if self.cuisine.core.file_exists("$cfgDir/geodns/dns/%s.json" % domain_name):
            content = self.cuisine.core.file_read("$cfgDir/geodns/dns/%s.json" % domain_name)
        domain_instance = Domain(domain_name, self.cuisine, serial, ttl, content, max_hosts, a_records, cname_records, ns)
        domain_instance.save()
        return domain_instance

    def get_domain(self, domain_name):
        """
        get domain object with dict of relevant records
        """
        if not self.cuisine.core.file_exists("$cfgDir/geodns/dns/%s.json" % domain_name):
            raise Exception("domain_name not created")
        return self.ensure_domain(domain_name)

    def del_domain(self, domain_name):
        """
        delete domain object
        """
        self.cuisine.core.dir_remove("$cfgDir/geodns/dns/%s.json" % domain_name)

    def add_record(self, domain_name, subdomain, record_type, value, weight=100):
        """
        @domain_name = domin object name : string
        @subdomain = subdomain assigned to record : string
        @record_type = cname or a :string
        @value = ip or cname : string
        @weight = recurrence on request : int
        """
        domain_instance = self.get_domain(domain_name)
        if record_type == "a":
            domain_instance.add_a_record(value, subdomain)
        if record_type == "cname":
            domain_instance.add_cname_record(value, subdomain)
        return domain_instance.save()



    def get_record(self, domain_name, record_type, subdomain=None):
        """
        returns a dict of record/s and related subdomains within domain
        """
        domain_instance = self.get_domain(domain_name)
        if record_type == "a":
            record = domain_instance.get_a_record(subdomain)
        if record_type == "cname":
            record = domain_instance.get_cname_record(subdomain)
        return record

    def del_record(self, domain_name, record_type, subdomain, value, full=True):
        """
        delete record and/or entire subdomain
        """
        domain_instance = self.get_domain(domain_name)
        if record_type == "a":
            domain_instance.del_a_record(subdomain=subdomain, ip=value, full=full)
        if record_type == "cname":
            domain_instance.del_cname_record(subdomain, value)
        return domain_instance.save()
