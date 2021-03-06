class DNS:
    def start(self):
        raise NotImplemented()
        
    def stop(self):
        raise NotImplemented()
    
    def restart(self):
        raise NotImplemented()
    
    def cleanCache(self):
        raise NotImplemented()
    
    def addRecord(self):
        raise NotImplemented()
    
    def deleteHost(self, host):
        raise NotImplemented()
    
    def updateHostIp(self, host, ip):
        raise NotImplemented()

    def zones(self):
        raise NotImplemented()
    
    def map(self):
        raise NotImplemented()
    
    def reversemap(self):
        raise NotImplemented()
    