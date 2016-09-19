# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_base import VmaxSmisBase
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking

if __name__ == '__main__':
    host = getenv("ECOM_IP", default="10.108.247.22")
    smis_base = VmaxSmisBase(host=host, port=5989, use_ssl=True)
    smis_masking = VmaxSmisMasking(smis_base=smis_base)

    systems = smis_base.list_storage_system_names()
    for s in systems:
        last = None
        unreferenced = []
        nohbas = []

        print 'smis_masking.list_hba_ids'
        hardware_ids = smis_masking.list_hba_ids()
        for h in hardware_ids:
            print str(h)

        print 'smis_masking.get_hba_instance_name'
        inst = smis_masking.get_hba_instance_name(h)
        print smis_base.dump_instance(smis_base.get_instance(inst))

        print 'smis_masking.list_ig_instance_ids'
        groups = smis_masking.list_ig_instance_ids(s)
        for ig in groups:
            last = ig
            print smis_masking.get_ig_name(s, ig)
            views = smis_masking.list_views_containing_ig(s, ig)
            if len(views) == 0:
                unreferenced.append(ig)

            hbas = smis_masking.list_initiators_in_ig(s, ig)
            if len(hbas) == 0:
                nohbas.append(ig)
            for hba in hbas:
                print '\t' + str(hba)

        if last is not None:
            print '\n' + smis_masking.get_ig_name(s, last)
            ig_inst = smis_masking.get_ig_instance(s, last)
            for i in ig_inst.items():
                print '\t' + str(i)

        print '\nEmpty Groups'
        for ig in nohbas:
            print smis_masking.get_ig_name(s, ig)

        print '\nNot in any masking view'
        for u in unreferenced:
            print smis_masking.get_ig_name(s, u)
