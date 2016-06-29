# Copyright 2016 EMC Corporation

from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices

if __name__ == '__main__':
    smis_base = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)
    smis_devices = VmaxSmisDevices(smis_base=smis_base)

    systems = smis_base.list_storage_system_names()
    for s in systems:
        print str(smis_base.find_storage_system(s))
        names = smis_devices.list_all_devices_by_name(s)
        name_hash = {}
        for n in names:
            if n in name_hash:
                count = name_hash[n] + 1
            else:
                count = 1
            name_hash[n] = count

        for n in name_hash.keys():
            if name_hash[n] > 1:
                print n + '\t' + str(name_hash[n])

        devs = smis_devices.list_all_devices(s)
        devs.extend(['009BF', '009C0'])
        for d in devs[-50:]:
            print '\t' + d + ': ' + smis_devices.get_volume_name(system_name=s, device_id=d)
            print '\t\t' + str(smis_devices.get_volume_size(system_name=s, device_id=d)/(1024*1024))
            print '\t\t' + str(smis_devices.get_storage_group(system_name=s, device_id=d))
        print 'Total count = ' + str(len(devs))

        print '\n'
        list = smis_devices.get_volume_properties(s, devs[-1], ['IsCompressed', 'IdentifyingDescriptions', 'EMCIsDeDuplicated' ])
        for key in list:
            print key + ': \t' + str(list[key])

        print '\n'
        pools = smis_devices.list_storage_pools(s)
        for p in pools:
                print str(p)

        rev = smis_devices.get_volume_by_name(s, names[-1])
        print '\n' + str(names[-1]) + ' ' + str(rev)
