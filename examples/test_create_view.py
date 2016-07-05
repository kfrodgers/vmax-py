# Copyright 2016 EMC Corporation

from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices


if __name__ == '__main__':
    smis_base = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)
    smis_devices = VmaxSmisDevices(smis_base=smis_base)

    system_name = smis_base.list_storage_system_names()[0]
    print str(system_name)

    pool_id = smis_devices.list_storage_pools(system_name)[0]
    print str(pool_id) + ' pool selected'

    wwn = u'iqn.1994-05.com.redhat:f3e6b941189b'
    try:
        hardware_id = smis_masking.get_storage_hardware_instance(wwn)
        print str(wwn) + ' already exists'
    except ReferenceError:
        hardware_id = smis_masking.create_storage_hardware_id(system_name, wwn)
        print str(hardware_id) + ' created'

    ig_name = u'kfr-test-ig'
    try:
        ig_id = smis_masking.get_ig_by_name(system_name, ig_name)
        print ig_name + ' already exists'
    except ReferenceError:
        ig_id = smis_masking.create_ig(system_name, ig_name, [wwn])
        print str(ig_id) + ' created'

    rc = smis_masking.remove_members_ig(system_name, ig_id, [hardware_id])
    rc = smis_masking.delete_ig(system_name, ig_id)
    print 'delete IG returned ' + str(rc)

    rc = smis_masking.delete_storage_hardware_id(system_name, hardware_id)
    print 'delete hardware id returned ' + str(rc)

    pg_name = u'kfr-test-pg'
    try:
        pg_id = smis_masking.get_pg_by_name(system_name, pg_name)
        print pg_name + ' PG alreay exists'
    except ReferenceError:
        directors = smis_masking.list_storage_directors(system_name)
        pg_id = smis_masking.create_pg(system_name, pg_name, [directors[-1]])
        print str(pg_id) + ' PG created'

    print str(smis_masking.list_directors_in_pg(system_name, pg_id))
    rc = smis_masking.remove_members_pg(system_name, pg_id, [directors[-1]])
    rc = smis_masking.delete_pg(system_name, pg_id)
    print 'delete PG ' + str(rc)

    exit(0)

    volume_name = u'kfr-volume-0001'
    try:
        device_instance = smis_devices.get_volume_by_name(system_name, volume_name)
        print str(device_instance) + ' already exists'
    except ReferenceError:
        device_instance = smis_devices.create_volume(system_name, volume_name, pool_id, 1024*1024*1024)
        print str(device_instance) + ' created'

    sg_name = u'kfr-test-sg'
    try:
        sg_id = smis_masking.get_sg_by_name(system_name, sg_name)
        print sg_name + ' alreay exists'
    except ReferenceError:
        sg_id = smis_masking.create_sg(system_name, sg_name)
        print str(sg_id) + ' created'

    rc = smis_masking.add_members_sg(system_name, sg_id, [device_instance])
    print 'add returned ' + str(rc)
    rc = smis_masking.remove_members_sg(system_name, sg_id, [device_instance])
    print 'remove returned ' + str(rc)
    rc = smis_masking.delete_sg(system_name, sg_id)
    print 'delete sg ' + str(rc)

    device_id = device_instance['DeviceId']
    rc = smis_devices.destroy_volume(system_name, device_id)
    print rc
