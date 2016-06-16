from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking


if __name__ == '__main__':
    smis_base = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)
    empty_groups = []

    systems = smis_base.list_storage_system_names()
    for s in systems:
        for sg in smis_masking.list_sg_instance_ids(s):
            devices = smis_masking.list_volumes_in_sg(s, sg)
            if len(devices) > 0:
                print smis_masking.get_sg_name(s, sg)
                for d in devices:
                    print '\t' + str(d['DeviceID'])
            else:
                empty_groups.append(sg)

        print '\n' + str(s) + ': Empty Storage Groups'
        for sg in empty_groups:
            print smis_masking.get_sg_name(s, sg)
            views = smis_masking.list_views_containing_sg(s, sg)
            if len(views) > 0:
                for v in views:
                    print '\t' + str(v)
            else:
                pass
