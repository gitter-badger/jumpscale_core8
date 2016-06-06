from amazon import AmazonProvider
from digitalocean import DigitalOcean



class Factory:
    self.__jslocation__="j.sal.cloudproviders"   

    def get(self, provider):
        '''Gets an instance of the cloud provider class
        @param provider: sting represents provider type, can be GOOGLE, AMAZON, DIGITALOCEAN, ...
        '''
        providers = {'AMAZON': AmazonProvider, 'DIGITALOCEAN': DigitalOcean}
        return providers[provider]()