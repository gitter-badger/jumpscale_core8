import re
from JumpScale import j


COMMAND = 'lsblk -bnP -o NAME,TYPE,UUID,FSTYPE,SIZE,MOUNTPOINT -e 7,1'

_extract_pattern = re.compile('\s*([^=]+)="([^"]*)"')


class LsblkError(Exception):
    pass


def _parse(output):
    """
    Parses the output of command
    `lsblk -abnP -o NAME,TYPE,UUID,FSTYPE,SIZE`

    Output must look like that
    NAME="sda" TYPE="disk" UUID="" FSTYPE="" SIZE="256060514304"
    NAME="sda1" TYPE="part" UUID="1db378f5-4e49-4fb7-8000-051fe77b23ea"
        FSTYPE="btrfs" SIZE="256059465728"
    NAME="sr0" TYPE="rom" UUID="" FSTYPE="" SIZE="1073741312"
    """
    blks = []
    for line in output.splitlines():
        if not line.strip():
            continue
        blk = dict(_extract_pattern.findall(line))
        blk['NAME'] = '/dev/%s' % blk['NAME']

        blks.append(blk)

    return blks


def lsblk(device=None):
    """
    Run lsblk on con, and returned the parsed results
    """
    _executor = j.tools.executor.getLocal()
    try:
        command = COMMAND
        if device:
            command = '%s %s' % (COMMAND, device)
        rc, output = _executor.execute(command)
    except Exception as e:
        raise LsblkError(e)

    return _parse(output)
