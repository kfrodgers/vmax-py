# Copyright 2016 EMC Corporation

from emc_vmax_smis.vmax_smis_base import VmaxSmisBase


if __name__ == '__main__':
    o = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)

    print '\nlist_storage_configuration_services()'
    stor = o.list_storage_configuration_services()
    for s in stor:
        print str(s)
        sys = o.find_storage_system(s['SystemName'])
        print '\t' + str(sys)

    print '\nlist_storage_system_names()'
    stor = o.list_storage_system_names()
    for s in stor:
        print str(s)
        print '\tIs V3 == ' + str(o.is_array_v3(s))

    print '\nlist_controller_configuration_services()'
    stor = o.list_controller_configuration_services()
    for s in stor:
        print str(s)

    print '\nlist_storage_software_identity()'
    stor = o.list_storage_software_identity()
    for s in stor:
        for item in s.items():
            print '\t' + str(item)

    print '\nlist_storage_hardwareid_services()'
    stor = o.list_storage_hardwareid_services()
    for s in stor:
        for item in s.items():
            print '\t' + str(item)

    print '\nlist_management_server_software_identity()'
    stor = o.list_management_server_software_identity()
    for s in stor:
        for item in s.items():
            print '\t' + str(item)
