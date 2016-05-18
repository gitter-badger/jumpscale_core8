
from JumpScale import j
import os
import time

import socket

from ActionDecorator import ActionDecorator
class actionrun(ActionDecorator):
    def __init__(self,*args,**kwargs):
        ActionDecorator.__init__(self,*args,**kwargs)
        self.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.proxy"


class CuisineProxy(object):
    """
    all methods to do to allow a local lan to work more efficient with internet e.g. cache for apt-get, web proxy, ...
    """

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine


    @actionrun(action=True)
    def installWebProxyServer(self):

        self.cuisine.fw.ufw_enable()
        self.cuisine.fw.allowIncoming(8123)

        self.cuisine.btrfs.subvolumeCreate("/storage/polipo_cache")            

        self.cuisine.package.install("polipo")

        forbiddentunnels="""
        # simple case, exact match of hostnames
        www.massfuel.com

        # match hostname against regexp
        \.hitbox\.

        # match hostname and port against regexp
        # this will block tunnels to example.com but also  www.example.com
        # for ports in the range 600-999
        # Also watch for effects of 'tunnelAllowedPorts'
        example.com\:[6-9][0-9][0-9]

        # random examples
        \.liveperson\.
        \.atdmt\.com
        .*doubleclick\.net
        .*webtrekk\.de
        ^count\..*
        .*\.offerstrategy\.com
        .*\.ivwbox\.de
        .*adwords.*
        .*\.sitestat\.com
        \.xiti\.com
        webtrekk\..*
        """
        self.cuisine.core.file_write("/etc/polipo/forbiddenTunnels",forbiddentunnels)

        # dnsNameServer

        CONFIG="""
            ### Basic configuration
            ### *******************

            # Uncomment one of these if you want to allow remote clients to
            # connect:

            # proxyAddress = "::0"        # both IPv4 and IPv6
            proxyAddress = "0.0.0.0"    # IPv4 only

            # If you do that, you'll want to restrict the set of hosts allowed to
            # connect:

            # allowedClients = 127.0.0.1, 134.157.168.57
            # allowedClients = 127.0.0.1, 134.157.168.0/24

            # Uncomment this if you want your Polipo to identify itself by
            # something else than the host name:

            # proxyName = "polipo.example.org"

            # Uncomment this if there's only one user using this instance of Polipo:

            # cacheIsShared = false

            # Uncomment this if you want to use a parent proxy:

            # parentProxy = "squid.example.org:3128"

            # Uncomment this if you want to use a parent SOCKS proxy:

            # socksParentProxy = "localhost:9050"
            # socksProxyType = socks5

            # Uncomment this if you want to scrub private information from the log:

            # scrubLogs = true


            ### Memory
            ### ******

            # Uncomment this if you want Polipo to use a ridiculously small amount
            # of memory (a hundred C-64 worth or so):

            # chunkHighMark = 819200
            # objectHighMark = 128

            # Uncomment this if you've got plenty of memory:

            chunkHighMark = 100331648
            objectHighMark = 16384


            ### On-disk data
            ### ************

            # Uncomment this if you want to disable the on-disk cache:

            # diskCacheRoot = ""

            # Uncomment this if you want to put the on-disk cache in a
            # non-standard location:

            diskCacheRoot = "/storage/polipo_cache/"

            # Uncomment this if you want to disable the local web server:

            # localDocumentRoot = ""

            # Uncomment this if you want to enable the pages under /polipo/index?
            # and /polipo/servers?.  This is a serious privacy leak if your proxy
            # is shared.

            # disableIndexing = false
            # disableServersList = false


            ### Domain Name System
            ### ******************

            # Uncomment this if you want to contact IPv4 hosts only (and make DNS
            # queries somewhat faster):

            # dnsQueryIPv6 = no

            # Uncomment this if you want Polipo to prefer IPv4 to IPv6 for
            # double-stack hosts:

            # dnsQueryIPv6 = reluctantly

            # Uncomment this to disable Polipo's DNS resolver and use the system's
            # default resolver instead.  If you do that, Polipo will freeze during
            # every DNS query:

            # dnsUseGethostbyname = yes


            ### HTTP
            ### ****

            # Uncomment this if you want to enable detection of proxy loops.
            # This will cause your hostname (or whatever you put into proxyName
            # above) to be included in every request:

            # disableVia=false

            # Uncomment this if you want to slightly reduce the amount of
            # information that you leak about yourself:

            # censoredHeaders = from, accept-language
            censorReferer = maybe

            # Uncomment this if you're paranoid.  This will break a lot of sites,
            # though:

            # censoredHeaders = set-cookie, cookie, cookie2, from, accept-language
            # censorReferer = true

            # Uncomment this if you want to use Poor Man's Multiplexing; increase
            # the sizes if you're on a fast line.  They should each amount to a few
            # seconds' worth of transfer; if pmmSize is small, you'll want
            # pmmFirstSize to be larger.

            # Note that PMM is somewhat unreliable.

            # pmmFirstSize = 16384
            # pmmSize = 8192

            # Uncomment this if your user-agent does something reasonable with
            # Warning headers (most don't):

            relaxTransparency = maybe

            # Uncomment this if you never want to revalidate instances for which
            # data is available (this is not a good idea):

            # relaxTransparency = yes

            # Uncomment this if you have no network:

            # proxyOffline = yes

            # Uncomment this if you want to avoid revalidating instances with a
            # Vary header (this is not a good idea):

            # mindlesslyCacheVary = true

            # Uncomment this if you want to add a no-transform directive to all
            # outgoing requests.

            # alwaysAddNoTransform = true

            disableIndexing = false

            """
        self.cuisine.core.file_write("/etc/polipo/config",CONFIG)


        self.cuisine.core.run("killall polipo",die=False)

        cmd=self.cuisine.core.run("which polipo")

        self.cuisine.processmanager.ensure("polipo",cmd)

        print ("INSTALL OK")
        print ("to see status: point webbrowser to")
        print ("http://%s:8123/polipo/status?"%self.cuisine.core.executor.addr)
        print ("configure your webproxy client to use %s on tcp port 8123"%self.cuisine.core.executor.addr)

        # self.cuisine.avahi.install()


    def configureClient(self,addr="",port=8123):
        if addr=="":
            addr=self.cuisine.executor.addr
        config='Acquire::http::Proxy "http://%s:%s";'%(addr,port)
        if self.cuisine.cuisine.platformtype.myplatform.startswith("ubuntu"):
            f=self.cuisine.core.file_read("/etc/apt/apt.conf","")
            f+="\n%s\n"%config
            self.cuisine.core.file_write("/etc/apt/apt.conf",f)
        else:
            raise RuntimeError("not implemented yet")
        from IPython import embed
        print ("DEBUG NOW configure client")
        embed()
        


    def __str__(self):
        return "cuisine.proxy:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))


    __repr__=__str__
