from JumpScale import j

descr = """
Checks Redis server status
"""

organization = "jumpscale"
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = True
roles = []

period = 600

log = True

def action():
    logger = j.logger.get('healthcheck_redis')
    ports = {}
    results = list()

    for instance in j.atyourservice.findServices(name='redis'):
        
        if not instance.isInstalled():
            continue
        
        for redisport in instance.getTCPPorts():
            if redisport:
                ports[instance.instance] = ports.get(instance.instance, [])
                ports[instance.instance].append(int(redisport))

    for instance, ports_val in ports.items():
        for port in ports_val:
            result = {'category': 'Redis'}
            pids = j.sal.process.getPidsByPort(port)
            errmsg = 'redis not operational[halted or not installed]'
            if not pids:
                state = 'ERROR'
                logger.warn_tb(j.exceptions.OPERATIONS, errmsg)
                used_memory = 0
                maxmemory = 0
            else:
                rcl = j.clients.redis.getByInstance(instance)
                if rcl.ping():
                    state = 'OK'
                else:
                    state = 'ERROR'
                    logger.warn_tb(j.exceptions.OPERATIONS, errmsg)

                maxmemory = float(rcl.config_get('maxmemory').get('maxmemory', 0))
                used_memory = rcl.info()['used_memory']
                size, unit = j.data.units.bytes.converToBestUnit(used_memory)
                msize, munit = j.data.units.bytes.converToBestUnit(maxmemory)
                used_memorymsg = '%.2f %sB' % (size, unit)
                maxmemorymsg = '%.2f %sB' % (msize, munit)               
                result['message'] = '*Port*: %s. *Memory usage*: %s/ %s' % (port, used_memorymsg, maxmemorymsg)

                if (used_memory / maxmemory) * 100 > 90:
                    state = 'WARNING'
                    logger.warn_tb(j.exceptions.OPERATIONS, result['message'])
      
            result['state'] = state
            results.append(result)
            print (results)

    return results

if __name__ == "__main__":
    print (action())

