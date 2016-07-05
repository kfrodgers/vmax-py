# Copyright 2016 EMC Corporation

from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking


if __name__ == '__main__':
    smis_base = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)
    smis_devices = VmaxSmisDevices(smis_base=smis_base)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)

    system_name = smis_base.list_storage_system_names()[0]
    print str(smis_base.find_storage_system(system_name))

    volume_names = smis_devices.list_all_devices_by_name(system_name)
    for volume_name in volume_names[-100:]:
        volume_inst = smis_devices.get_volume_by_name(system_name, volume_name)
        storage_groups = smis_devices.get_storage_group(system_name, volume_inst['DeviceID'])
        if len(storage_groups) == 0:
            continue
        for sg_inst_id in storage_groups:
            views = smis_masking.list_views_containing_sg(system_name, sg_inst_id)
            for mv in views:
                initiators = smis_masking.list_initiators_in_view(system_name, mv)
                print '\n' + volume_name + ':'
                for initiator in initiators:
                    print '\t' + initiator



