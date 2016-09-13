# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_sync import VmaxSmisSync

def do_print(instance):
    for s in instance:
        print '\t' + str(s)
        for item in s.items():
            print '\t\t' + str(item)


if __name__ == '__main__':
    host = getenv("ECOM_IP", default="10.108.247.22")
    smis_sync = VmaxSmisSync(host=host, port=5989, use_ssl=True)

    system_names = smis_sync.smis_base.list_storage_system_names()
    for s in system_names:
        print 'System name: ' + str(s)
        sync_sources = smis_sync.get_sync_sv_source_devices(s)
        print 'Sources'
        for source in sync_sources:
            svcs = smis_sync.get_sync_sv_by_source(s, source)
            print str(source)
            for svc in svcs:
                print '\t-->' + smis_sync.get_sync_target(svc)['deviceid']
        sync_targets = smis_sync.get_sync_sv_target_devices(s)
        print 'Targets'
        for target in sync_targets:
            svc = smis_sync.get_sync_sv_by_target(s, target)
            print str(target) + '\n\t<--' + smis_sync.get_sync_source(svc)['deviceid']
