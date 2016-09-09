# Copyright 2016 EMC Corporation

from os import getenv
from emc_vmax_smis.vmax_smis_base import VmaxSmisBase

def do_print(name):
    inst = smis_base.get_instance(name)
    print name
    for item in inst.items():
        print '\t' + str(item)


if __name__ == '__main__':
    host = getenv("ECOM_IP", default="10.108.247.22")
    smis_base = VmaxSmisBase(host=host, port=5989, use_ssl=True)

    system_names = smis_base.list_storage_system_names()
    for s in system_names:
        vps = smis_base.list_virtual_provisioning_pools()
        for vp in vps:
            if s in vp['InstanceID']:
                do_print(vp)

        srps = smis_base.list_srp_storage_pools()
        for srp in srps:
            if s in srp['InstanceID']:
                do_print(srp)
