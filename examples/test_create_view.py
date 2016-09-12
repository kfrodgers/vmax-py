# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices


if __name__ == '__main__':
    host = getenv("ECOM_IP", default="10.108.247.22")
    smis_base = VmaxSmisBase(host=host, port=5989, use_ssl=True)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)
    smis_devices = VmaxSmisDevices(smis_base=smis_base)

    system_name = smis_base.list_storage_system_names()[0]
    print str(system_name)

    pool_id = smis_devices.list_storage_pools(system_name)[0]
    print str(pool_id) + ' pool selected'

    wwn = u'iqn.1994-05.com.redhat:f3e6b941189b'
    try:
        hardware_id = smis_masking.get_hba_id(wwn)
        print str(hardware_id) + ' HBA already exists'
    except ReferenceError:
        hardware_id = smis_masking.create_hba_id(system_name, wwn)
        print str(hardware_id) + ' HBA created'

    ig_name = u'kfr-test-ig'
    try:
        ig_id = smis_masking.get_ig_by_name(system_name, ig_name)
        print ig_name + ' IG already exists'
    except ReferenceError:
        ig_id = smis_masking.create_ig(system_name, ig_name, [hardware_id])
        print str(ig_id) + ' IG created'

    pg_name = u'kfr-test-pg'
    try:
        pg_id = smis_masking.get_pg_by_name(system_name, pg_name)
        print pg_name + ' PG alreay exists'
    except ReferenceError:
        directors = smis_masking.list_storage_directors(system_name)
        pg_id = smis_masking.create_pg(system_name, pg_name, [directors[-1]])
        print str(pg_id) + ' PG created'

    volume_name = u'kfr-volume-0001'
    try:
        new_device = smis_devices.get_volume_by_name(system_name, volume_name)
        print str(new_device) + ' volume already exists'
    except ReferenceError:
        new_device = smis_devices.create_volume(system_name, volume_name, pool_id, 1024*1024*1024)
        print str(new_device) + ' volume created'

    sg_name = u'kfr-test-sg'
    try:
        sg_id = smis_masking.get_sg_by_name(system_name, sg_name)
        print sg_name + ' alreay exists'
    except ReferenceError:
        device_instances = smis_devices.get_volume_instance_names(system_name, [new_device])
        sg_id = smis_masking.create_sg(system_name, sg_name, device_instances)
        print str(sg_id) + ' created'

    device_ids = smis_masking.list_volumes_in_sg(system_name, sg_id)
    device_instances = smis_devices.get_volume_instance_names(system_name, device_ids)
    rc = smis_masking.remove_members_sg(system_name, sg_id, device_instances)
    rc = smis_masking.delete_sg(system_name, sg_id)
    print 'delete SG ' + str(rc)

    rc = smis_devices.destroy_volumes(system_name, device_ids)
    print 'delete volumes returned ' + str(rc)

    rc = smis_masking.remove_members_ig(system_name, ig_id, [hardware_id])
    rc = smis_masking.delete_ig(system_name, ig_id)
    print 'delete IG returned ' + str(rc)

    rc = smis_masking.delete_hba_id(system_name, hardware_id)
    print 'delete hardware id returned ' + str(rc)

    members = smis_masking.list_directors_in_pg(system_name, pg_id)
    rc = smis_masking.remove_members_pg(system_name, pg_id, members)
    rc = smis_masking.delete_pg(system_name, pg_id)
    print 'delete PG ' + str(rc)
