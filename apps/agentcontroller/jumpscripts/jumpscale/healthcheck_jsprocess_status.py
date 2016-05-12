

from JumpScale import j

descr = """
Check if all jsprocesses are running
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
log = True
queue ='process'
roles = []


def action():
    logger = j.logger.get('healthcheck_jsprocess_status')
    results =list()
    for ays in j.atyourservice.findServices():
        if not ays.getProcessDicts():
                continue
        result = dict()
        result['state'] = 'OK'
        result['message'] = "Process %s:%s:%s " % (ays.domain, ays.name, ays.instance)
        result['category'] = 'AYS Process'
        if not ays.actions.check_up_local(ays, wait=False):
            message = "Process %s:%s:%s is halted" % (ays.domain, ays.name, ays.instance)
            logger.warn_tb(j.exceptions.OPERATIONS, message, level=2)
            result['state'] = 'HALTED'
            result['message'] = message
            result['category'] = 'AYS Process'
        results.append(result)
            
    return results
         
if __name__ == '__main__':
    print(action())
