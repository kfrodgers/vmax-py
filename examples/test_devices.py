# Copyright 2016 EMC Corporation

from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices

if __name__ == '__main__':
    smis_base = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)
    smis_devices = VmaxSmisDevices(smis_base=smis_base)

    systems = smis_base.list_storage_system_names()
    for s in systems:
        print str(smis_base.find_storage_system(s))
        devs = smis_devices.list_all_devices(s)
        for d in devs[-10:]:
            print '\t' + d + '\t' + str(smis_devices.get_volume_size(system_name=s, device_id=d)/(1024*1024))
            print '\t\t' + str(smis_devices.get_storage_group(system_name=s, device_id=d))
        print 'Total count = ' + str(len(devs))

        req = [u'ThinlyProvisioned', u'NameFormat', u'Caption', u'StorageTieringSelection',
               u'EMCIsDeDuplicated', u'DeviceID', u'NoSinglePointOfFailure']
        print str(smis_devices.get_volume_properties(s, devs[-1], req))
