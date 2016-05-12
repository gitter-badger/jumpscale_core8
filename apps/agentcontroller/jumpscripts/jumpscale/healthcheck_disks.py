from JumpScale import j

descr = """
Checks disks' status
"""

organization = "jumpscale"
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = True
queue = 'process'
roles = []
enable = True
period = 600

log = True


def action():
    logger = j.logger.get('healthcheck_disk')
    result = dict()
    pattern = None

    if j.application.config.exists('gridmonitoring.disk.pattern'):
        pattern = j.application.config.getStr('gridmonitoring.disk.pattern')

    disks = j.sal.diskmanager.partitionsFind(
        mounted=True, prefix='', minsize=0, maxsize=None)

    def diskfilter(disk):
        return not (pattern and j.codetools.regex.match(pattern, disk.path))

    def disktoStr(disk):
        if disk.mountpoint:
            freesize, freeunits = j.data.units.bytes.converToBestUnit(disk.free, 'M')
            size = j.data.units.bytes.toSize(disk.size, 'M', freeunits)
            return "%s on %s %.02f/%.02f %siB free" % (disk.path, disk.mountpoint, freesize, size, freeunits)
        else:
            return '%s %s' % (disk.path, disk.model)

    results = list()
    for disk in filter(diskfilter, disks):
        result = {'category': 'Disks'}
        result['path'] = disk.path
        checkusage = not (disk.mountpoint and j.sal.fs.exists(j.sal.fs.joinPaths(disk.mountpoint, '.dontreportusage')))
        result['state'] = 'OK'
        result['message'] = disktoStr(disk)
        if disk.free and disk.size:
            freepercent = (disk.free / float(disk.size)) * 100
            if checkusage and (freepercent < 10):
                logger.warn_tb(j.exceptions.OPERATIONS, result['message'], level=2)
                result['state'] = 'WARNING'
            if checkusage and (freepercent < 5):
                logger.warn_tb(j.exceptions.OPERATIONS, result['message'])
                result['state'] = 'ERROR'
        results.append(result)

    if not results:
        results.append({'message': 'No disks available', 'state': 'OK', 'category': 'Disks'})

    return results

if __name__ == "__main__":
    print (action())
