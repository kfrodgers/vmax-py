# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_base import VmaxSmisBase


if __name__ == '__main__':
    host = getenv("ECOM_IP", default="10.108.247.22")
    smis_base = VmaxSmisBase(host=host, port=5989, use_ssl=True)
    print '\tValid SE Version == ' + str(smis_base.check_se_version())

    print '\nlist_storage_configuration_services()'
    stor = smis_base.list_storage_configuration_services()
    for s in stor:
        print str(s)
        sys = smis_base.find_storage_system(s['SystemName'])
        print '\t' + str(sys)

    print '\nlist_storage_system_names()'
    stor = smis_base.list_storage_system_names()
    for s in stor:
        print str(s)
        print '\tIs V3 == ' + str(smis_base.is_array_v3(s))

    print '\nlist_storage_iscsi_enpoints()'
    stor = smis_base.list_storage_iscsi_enpoints()
    for s in stor:
        print str(s)

    print '\nlist_storage_system_instance_names'
    stor = smis_base.list_storage_system_instance_names()
    for s in stor:
        pools = smis_base.find_virtual_provisioning_pool(s)
        for p in pools:
            inst = smis_base.get_instance(p)
            print '\tPOOL == ' + str(inst['ElementName'])
            print '\t' + str(p)
        pools = smis_base.find_srp_storage_pool(s)
        for p in pools:
            print '\tSRP == ' + str(p)

    print '\nlist_controller_configuration_services()'
    stor = smis_base.list_controller_configuration_services()
    for s in stor:
        print str(s)

    print '\nlist_storage_software_identity()'
    stor = smis_base.list_storage_software_identity()
    for s in stor:
        for item in s.items():
            print '\t' + str(item)

    print '\nlist_storage_hardwareid_services()'
    stor = smis_base.list_storage_hardwareid_services()
    for s in stor:
        for item in s.items():
            print '\t' + str(item)

    print '\nlist_management_server_software_identity()'
    stor = smis_base.list_management_server_software_identity()
    for s in stor:
        for item in s.items():
            print '\t' + str(item)

    print '\nlist_all_initiators()'
    stor = smis_base.list_all_initiators()
    for s in stor:
        print '\t' + str(s.path)
        inst = smis_base.get_instance(s.path)
        for i in inst.items():
            print '\t\t' + unicode(i)
        for ig in smis_base.find_initiator_groups(s.path):
            print '\t\t' + str(ig)
            inst = smis_base.get_instance(ig)
            for i in inst.items():
                print '\t\t\t' + unicode(i)
