# Copyright 2016 EMC Corporation

from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices

if __name__ == '__main__':
    smis_base = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)
    smis_devices = VmaxSmisDevices(smis_base=smis_base)

    #
    # For every system list devices that are not in an SG, limit
    # to 200 newest devices
    #
    systems = smis_base.list_storage_system_names()
    for sys in systems:
        print str(smis_base.find_storage_system(sys))

        devs = smis_devices.list_all_devices(sys)
        print 'Total count = ' + str(len(devs))
        for d in devs[-200:]:
            sg_names = smis_devices.get_storage_group(system_name=sys, device_id=d)
            if sg_names is None or len(sg_names) == 0:
                name = smis_devices.get_volume_name(system_name=sys, device_id=d)
                size = str(smis_devices.get_volume_size(system_name=sys, device_id=d))
                print '\t' + d + ': ' + name + ' (sizeBytes=' + size + ')'
