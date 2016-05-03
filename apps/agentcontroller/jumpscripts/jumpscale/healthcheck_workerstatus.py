from JumpScale import j

descr = """
Monitor CPU and mem of worker
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"
async = True
roles = []
period = 600
log = True


def action():
    logger = j.logger.get('healthcheck_workerstatus')
    rediscl = j.clients.redis.getByInstance('system')
    timemap = {'default': '-2m', 'io': '-2h', 'hypervisor': '-10m', 'process': '-1m'}
    results = list()

    for queue in ('io', 'hypervisor', 'default', 'process'):
        result = {'category': 'Workers'}
        lastactive = float(rediscl.hget('workers:heartbeat', queue) or 0)
        timeout = timemap.get(queue)
        lastactiv = '{{ts:%s}}' % lastactive if lastactive else 'never'
        result['message'] = '*%s last active*: %s' % (queue.upper(), lastactiv)
        if j.base.time.getEpochAgo(timeout) < lastactive:
            result['state'] = 'OK'
        else:
            logger.warn_tb(j.exceptions.OPERATIONS, result['message'])
            result['state'] = 'ERROR'


        results.append(result)
    return results

if __name__ == "__main__":
    print (action())
