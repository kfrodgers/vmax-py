# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking


if __name__ == '__main__':
    host = getenv("ECOM_IP", default="10.108.247.22")
    smis_base = VmaxSmisBase(host=host, port=5989, use_ssl=True)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)
    empty_groups = []
    unrefed_groups = []

    systems = smis_base.list_storage_system_names()
    for s in systems:
        for sg in smis_masking.list_sg_instance_ids(s):
            devices = smis_masking.list_volumes_in_sg(s, sg)
            if len(devices) > 0:
                print smis_masking.get_sg_name(s, sg)
                for d in devices:
                    print '\t' + str(d)
            else:
                empty_groups.append(sg)

            views = smis_masking.list_views_containing_sg(s, sg)
            if len(views) == 0:
                unrefed_groups.append(sg)

        print '\n' + str(s) + ': Storage Groups not in View'
        for sg in unrefed_groups:
            print smis_masking.get_sg_name(s, sg)

        print '\n' + str(s) + ': Empty Storage Groups'
        for sg in empty_groups:
            print smis_masking.get_sg_name(s, sg)

        print '\n' + str(s) + ': List Storage Directors'
        for storage_dir in smis_masking.list_storage_directors(s):
            print str(storage_dir)
