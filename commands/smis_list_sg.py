#! /usr/bin/python
# Copyright 2016 EMC Corporation

import os
import sys
import getopt
from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking

PROGNAME = os.path.basename(sys.argv[0])
USAGE = ('Usage: {0} '
         '-h <host>|--host <host> '
         '-s <symm_id>|--sid <symm_id> '
         '[-u <username>|--user <username>] '
         '[-p <password>|--password <password>] '
         '[-S|--use_ssl]\n'.format(PROGNAME))


def usage():
    sys.stderr.write(USAGE)
    sys.exit(2)


def main():
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'h:s:u:p:S',
                                           ['host=', 'sid=', 'user=', 'password=', 'use_ssl'])
    except getopt.GetoptError as err:
        sys.stderr.write('{0!s}\n'.format(err))
        usage()

    host = os.getenv('SMIS_HOST', None)
    sid = os.getenv('SMIS_SID', None)
    user = os.getenv('SMIS_USER', 'admin')
    password = os.getenv('SMIS_PASSWORD', '#1Password')
    use_ssl = False
    port = 5988
    for opt, arg in options:
        if opt in ('-h', '--host'):
            host = arg
        elif opt in ('-s', '--sid'):
            sid = arg
        elif opt in ('-u', '--user'):
            user = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-S', '--use_ssl'):
            use_ssl = True
            port = 5989
        else:
            usage()

    if host is None or sid is None:
        usage()

    smis_base = VmaxSmisBase(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)

    for system_name in smis_base.list_storage_system_names():
        if system_name.endswith(sid):
            break
    else:
        raise ReferenceError('%s: symmetrix id not found' % sid)

    for sg in smis_masking.list_sg_instance_ids(system_name):
        print smis_masking.get_sg_name(system_name, sg)
        devices = smis_masking.list_volumes_in_sg(system_name, sg)
        if len(devices) > 0:
            start = 0
            while start < len(devices):
                print '\t' + str(devices[start:start+10])
                start += 10


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
