# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_sync import VmaxSmisSync

def do_print(name, props):
    print str(name)
    for k in sorted(props.keys()):
        print '\t' + k + ' = ' + str(props[k])


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
            for svc in svcs:
                props = smis_sync.get_sync_sv_properties(svc)
                do_print(svc, props)

        sync_targets = smis_sync.get_sync_sv_target_devices(s)
        print 'Targets'
        for target in sync_targets:
            svc = smis_sync.get_sync_sv_by_target(s, target)
            props = smis_sync.get_sync_sv_properties(svc)
            do_print(svc, props)
