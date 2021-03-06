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
        endpoints = smis_masking.list_storage_directors(s)
        for e in endpoints:
            print str(e)

        inst_name = smis_masking.get_storage_director_by_name(s, e)
        inst = smis_base.get_instance(inst_name)
        print smis_base.dump_instance(inst)

        print '\n'
        last = ''
        unrefed_groups = []

        groups = smis_masking.list_pg_instance_ids(s)
        for pg in groups:
            last = smis_masking.get_pg_name(s, pg)
            print last
            for port in smis_masking.list_directors_in_pg(s, pg):
                print '\t' + str(port)

            views = smis_masking.list_views_containing_pg(s, pg)
            if len(views) == 0:
                unrefed_groups.append(pg)

        print '\n' + str(smis_masking.get_pg_by_name(s, last))

        print '\nPort Groups not in View'
        for pg in unrefed_groups:
            print smis_masking.get_pg_name(s, pg)