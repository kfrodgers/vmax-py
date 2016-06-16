from emc_vmax_smis.vmax_smis_base import VmaxSmisBase

if __name__ == '__main__':
    o = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)

    masking_views = o.list_masking_views()
    for mv in masking_views:
        print str(mv)
        print '\t' + str(o.list_initiator_group_in_view(mv))
        print '\t' + str(o.list_port_group_in_view(mv))
        print '\t' + str(o.list_storage_group_in_view(mv))
