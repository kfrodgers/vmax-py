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

    volume_name = 'kfr-volume-0001'
    pool_id = smis_devices.list_storage_pools(system_name)[0]
    try:
        device_instance = smis_devices.get_volume_by_name(system_name, volume_name)
        print str(device_instance) + ' already exists'
    except Exception as e:
        device_instance = smis_devices.create_volume(system_name, volume_name, pool_id, 1024*1024)

    device_id = device_instance['DeviceId']
    rc = smis_devices.destroy_volume(system_name, device_id)
    print rc

    sg_name = 'kfr-test-sg'
    sg_list = smis_masking.list_sg_instance_ids(system_name)
    for sg in sg_list:
        if sg_name in sg:
            print sg_name + ' alreay exists, deleting'
            rc = smis_masking.delete_sg(system_name, sg)
            print rc
            break
    else:
        new_id = smis_masking.create_sg(system_name, sg_name)
        print str(new_id)
        rc = smis_masking.delete_sg(system_name, new_id)
        print rc

    pg_name = 'kfr-test-pg'
    pg_list = smis_masking.list_pg_instance_ids(system_name)
    for pg in pg_list:
        if pg_name in pg:
            print pg_name + ' alreay exists, deleting'
            rc = smis_masking.delete_pg(system_name, pg)
            print rc
            break
    else:
        directors = smis_masking.list_storage_directors(system_name)
        new_id = smis_masking.create_pg(system_name, pg_name, [ directors[-1] ])
        print str(new_id)
        print str(smis_masking.list_directors_in_pg(system_name, new_id))
        rc = smis_masking.delete_pg(system_name, new_id)
        print rc