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
        masking_views = smis_masking.list_mv_instance_ids(s)
        for mv in masking_views:
            print str(mv)
            sgs = smis_masking.list_sgs_in_view(s, mv)
            for sg in sgs:
                print '\t' + str(sg)
                items = smis_masking.list_volumes_in_sg(s, sg)
                print '\t\t' + str(items)
            pgs = smis_masking.list_pgs_in_view(s, mv)
            for pg in pgs:
                print '\t' + str(pg)
                items = smis_masking.list_directors_in_pg(s, pg)
                print '\t\t' + str(items)
            igs = smis_masking.list_igs_in_view(s, mv)
            for ig in igs:
                print '\t' + str(ig)
                items = smis_masking.list_initiators_in_ig(s, ig)
                print '\t\t' + str(items)
