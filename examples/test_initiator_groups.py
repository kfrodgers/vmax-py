from emc_vmax_smis.vmax_smis_base import VmaxSmisBase

if __name__ == '__main__':
    o = VmaxSmisBase(host='10.108.247.22', port=5989, use_ssl=True)

    empty_groups = []

    groups = o.list_initiator_groups()

    for ig in groups:
        views = o.list_views_for_initiator_group(ig)
        if len(views) > 0:
            print str(ig)
            for v in views:
                print '\t' + str(v)

    for e in groups:
        print str(e)
        initiators = o.list_initiators_in_group(e)
        for i in initiators:
            print '\t' + str(i)
        if len(initiators) == 0:
            empty_groups.append(i)

    print '\nEmpty Groups'
    for e in empty_groups:
        print str(e)

    print len(empty_groups)
