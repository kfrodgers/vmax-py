# Copyright 2016 EMC Corporation

import os
import sys
import platform
import getopt
from uuid import uuid4
from bitmath import GiB
from emc_vmax_smis.vmax_smis_masking import VmaxSmisMasking
from emc_vmax_smis.vmax_smis_devices import VmaxSmisDevices
from emc_vmax_smis.vmax_smis_sync import VmaxSmisSync, SMIS_TYPE_Clone

BASE_PARAMETERS = [('--host', True, os.getenv('SMIS_HOST', None), None),
                   ('--sid', True, os.getenv('SMIS_SID', None), None),
                   ('--user', True, os.getenv('SMIS_USER', 'admin'), None),
                   ('--password', True, os.getenv('SMIS_PASSWORD', '#1Password'), None),
                   ('--port', True, 5988, None),
                   ('--usessl', False, os.getenv('SMIS_SSL', 'False'), None)]


def get_paramter(input_opt, parameter_list):
    for i in range(0, len(parameter_list)):
        opt, has_argument, default_value, current_value = parameter_list[i]
        if opt == input_opt:
            value = current_value
            break
    else:
        raise AttributeError('%s: Unknown parameter' % input_opt)

    return value


def set_paramter(input_opt, input_value, parameter_list):
    for i in range(0, len(parameter_list)):
        opt, has_argument, default_value, current_value = parameter_list[i]
        if opt == input_opt:
            if has_argument:
                parameter_list[i] = (opt, has_argument, default_value, input_value)
            else:
                current_value = str(not eval(current_value))
                parameter_list[i] = (opt, has_argument, default_value, current_value)
            break
    else:
        raise AttributeError('%s: Unknown parameter' % input_opt)


def getopt_wrapper(parameter_list):
    getopt_params = []
    usage_message = ''
    for i in range(0, len(parameter_list)):
        opt, has_argument, default_value, current_value = parameter_list[i]
        param = opt[2:]
        usage_message = '%s %s' % (usage_message, opt)
        if has_argument:
            usage_message = '%s=<%s>' % (usage_message, opt[2:])
            param += '='
        if default_value is not None:
            current_value = default_value
        getopt_params.append(param)
        parameter_list[i] = (opt, has_argument, default_value, current_value)

    try:
        options, remainder = getopt.getopt(sys.argv[1:], '', getopt_params)
    except getopt.GetoptError as err:
        sys.stderr.write('{0!s}\n'.format(err))
        usage(usage_message)
        sys.exit(2)

    for opt, arg in options:
        try:
            set_paramter(opt, arg, parameter_list)
        except AttributeError:
            usage(usage_message)
            sys.exit(2)

    for i in range(0, len(parameter_list)):
        opt, has_argument, default_value, current_value = parameter_list[i]
        if current_value is None:
            sys.stderr.write('Error: Missing param %s\n' % opt)
            usage(usage_message)
            sys.exit(2)

    return remainder


def usage(usage_message):
    program_name = os.path.basename(sys.argv[0])
    sys.stderr.write('Usage: %s %s\n' % (program_name, usage_message))


def find_symmetrix(smis_base, sid):
    for system_name in smis_base.list_storage_system_names():
        if system_name.endswith(sid):
            break
    else:
        raise ReferenceError('%s: symmetrix id not found' % sid)
    return system_name


def add_devs():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--size', True, '1', None),
                           ('--count', True, '1', None),
                           ('--name', True, platform.node().split('.')[0], None),
                           ('--pool', True, None, None)])

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989
    name = get_paramter('--name', parameter_list)
    pool = get_paramter('--pool', parameter_list)
    size = int(get_paramter('--size', parameter_list))
    count = int(get_paramter('--count', parameter_list))

    smis_devices = VmaxSmisDevices(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)

    system_name = find_symmetrix(smis_devices.smis_base, sid)

    storage_pools = smis_devices.list_storage_pools(system_name)
    for storage_pool in storage_pools:
        pool_inst = smis_devices.get_pool_instance(system_name, storage_pool)
        if pool == pool_inst['ElementName']:
            break
    else:
        raise ReferenceError('%s: pool not found or not specified' % pool)

    volume_name = name + '-' + str(uuid4())
    device_ids = smis_devices.create_volumes(system_name, volume_name, storage_pool,
                                             int(GiB(size).to_Byte().value), count=count)
    print str(device_ids)


def add_mv():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--sg', True, None, None),
                           ('--pg', True, None, None),
                           ('--ig', True, None, None),
                           ('--name', True, platform.node().split('.')[0], None)])

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989
    name = get_paramter('--name', parameter_list)
    sg_name = get_paramter('--sg', parameter_list)
    pg_name = get_paramter('--pg', parameter_list)
    ig_name = get_paramter('--ig', parameter_list)

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)

    system_name = find_symmetrix(smis_masking.smis_base, sid)

    masking_views = smis_masking.list_mv_instance_ids(system_name)
    if name in masking_views:
        print '%s : MV already exists' % name
        sys.exit(1)

    smis_masking.create_masking_view(system_name, name, ig_name, sg_name, pg_name)


def del_devs():
    parameter_list = BASE_PARAMETERS

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_devices = VmaxSmisDevices(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    smis_sync = VmaxSmisSync(smis_base=smis_devices.smis_base)
    system_name = find_symmetrix(smis_devices.smis_base, sid)

    sync_sources = smis_sync.get_sync_sv_source_devices(system_name)
    sync_targets = smis_sync.get_sync_sv_target_devices(system_name)

    del_volumes = []
    for dev_id in remainder:
        while len(dev_id) < 5:
            dev_id = '0' + dev_id

        dev_id = dev_id.upper()
        if dev_id in sync_sources:
            print dev_id + ' is sync source, skipping delete'
            continue

        if dev_id in sync_targets:
            print dev_id + ' is sync target, breaking sync relationship'
            sync_svs = smis_sync.get_sync_sv_by_device(system_name, dev_id)
            props = smis_sync.get_sync_sv_properties(sync_svs[0], property_list=['SyncType'])
            if props['SyncType'] == SMIS_TYPE_Clone:
                smis_sync.detach_sync_relationship(system_name, sync_svs[0])
            else:
                smis_sync.deactivate_sync_relationship(system_name, sync_svs[0])

        try:
            smis_devices.get_volume_instance(system_name, dev_id)
            del_volumes.append(dev_id)
        except ReferenceError:
            print dev_id + ' not found'

    if len(del_volumes) > 0:
        print 'deleting ' + str(del_volumes)
        smis_devices.destroy_volumes(system_name, del_volumes)


def del_mv():
    parameter_list = BASE_PARAMETERS

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    for name in remainder:
        masking_views = smis_masking.list_mv_instance_ids(system_name)
        if name not in masking_views:
            print '%s : MV not found' % name
            sys.exit(1)

        smis_masking.delete_masking_view(system_name, name)


def list_devs():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--mapped', False, 'False', None),
                           ('--unmapped', False, 'False', None),
                           ('--name', True, '', None)])

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989
    name = get_paramter('--name', parameter_list)
    mapped_only = eval(get_paramter('--mapped', parameter_list))
    unmapped_only = eval(get_paramter('--unmapped', parameter_list))

    if mapped_only and unmapped_only:
        sys.exit(2)

    smis_devices = VmaxSmisDevices(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)

    system_name = find_symmetrix(smis_devices.smis_base, sid)

    for dev_id in smis_devices.list_all_devices(system_name):
        volume = smis_devices.get_volume_instance(system_name, dev_id)
        if (len(name) is 0 or volume['ElementName'].startswith(name)) \
                and (mapped_only is False or volume['EMCIsMapped'] is True) \
                and (unmapped_only is False or volume['EMCIsMapped'] is False):
            print str(dev_id) + '\tName=' + volume['ElementName'] + \
                  '\tIsMapped=' + str(volume['EMCIsMapped']) + \
                  '\tIsComposite=' + str(volume['IsComposite'])


def list_dirs():
    parameter_list = BASE_PARAMETERS

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    for director in smis_masking.list_storage_directors(system_name):
        print director


def list_igs():
    parameter_list = BASE_PARAMETERS

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    for ig in smis_masking.list_ig_instance_ids(system_name):
        print smis_masking.get_ig_name(system_name, ig)
        initiators = smis_masking.list_initiators_in_ig(system_name, ig)
        if len(initiators) > 0:
            for i in initiators:
                print '\t' + str(i)


def list_mvs():
    parameter_list = BASE_PARAMETERS

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    for mv in smis_masking.list_mv_instance_ids(system_name):
        print mv
        for sg in smis_masking.list_sgs_in_view(system_name, mv):
            print '\tSG: ' + smis_masking.get_sg_name(system_name, sg)
        for pg in smis_masking.list_pgs_in_view(system_name, mv):
            print '\tPG: ' + smis_masking.get_pg_name(system_name, pg)
        for ig in smis_masking.list_igs_in_view(system_name, mv):
            print '\tIG: ' + smis_masking.get_ig_name(system_name, ig)


def list_pgs():
    parameter_list = BASE_PARAMETERS

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    for pg in smis_masking.list_pg_instance_ids(system_name):
        print smis_masking.get_pg_name(system_name, pg)
        dirs = smis_masking.list_directors_in_pg(system_name, pg)
        if len(dirs) > 0:
            for d in dirs:
                print '\t' + str(d)


def list_pools():
    parameter_list = BASE_PARAMETERS

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_devices = VmaxSmisDevices(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_devices.smis_base, sid)

    for storage_pool in smis_devices.list_storage_pools(system_name):
        pool_inst = smis_devices.get_pool_instance(system_name, storage_pool)
        print pool_inst['ElementName']


def list_sgs():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--name', True, '', None)])

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    name = get_paramter('--name', parameter_list)
    if use_ssl and port == 5988:
        port = 5989

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    batch_size = 6
    for sg in smis_masking.list_sg_instance_ids(system_name):
        sg_name = smis_masking.get_sg_name(system_name, sg)
        if len(name) is 0 or sg_name.startswith(name):
            print sg_name
            devices = smis_masking.list_volumes_in_sg(system_name, sg)
            if len(devices) > 0:
                start = 0
                while start < len(devices):
                    print '\t' + str(devices[start:start+batch_size])
                    start += batch_size


def list_unmapped_devs():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--name', True, '', None)])

    getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    name = get_paramter('--name', parameter_list)
    if use_ssl and port == 5988:
        port = 5989

    smis_devices = VmaxSmisDevices(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_devices.smis_base, sid)

    for dev_id in smis_devices.list_all_devices(system_name):
        volume = smis_devices.get_volume_instance(system_name, dev_id)
        if (len(name) is 0 or volume['ElementName'].startswith(name)) \
                and volume['EMCIsMapped'] is False and volume['IsComposite'] is False \
                and volume['Usage'] not in [12, 14, 18]:
            storage_groups = smis_devices.get_storage_group(system_name, dev_id)
            if len(storage_groups) == 0:
                print str(dev_id) + '\tName=' + volume['ElementName']


def mod_ig():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--name', True, None, None),
                           ('--create', True, 'False', None),
                           ('--delete', True, 'False', None),
                           ('--add', True, 'False', None),
                           ('--remove', True, 'False', None)])

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    ig_name = get_paramter('--name', parameter_list)
    if use_ssl and port == 5988:
        port = 5989
    is_create = eval(get_paramter('--create', parameter_list))
    is_add = eval(get_paramter('--delete', parameter_list))
    is_remove = eval(get_paramter('--add', parameter_list))
    is_delete = eval(get_paramter('--remove', parameter_list))

    if is_add == is_remove or (is_create and is_delete):
        sys.exit(1)

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    try:
        initiator_group_id = smis_masking.get_ig_by_name(system_name, ig_name)
        if is_create:
            print '%s: IG already exists' % ig_name
            sys.exit(1)
    except ReferenceError:
        if is_create:
            initiator_group_id = smis_masking.create_ig(system_name, ig_name)
        else:
            print '%s : IG not found' % ig_name
            sys.exit(1)

    if is_delete:
        views = smis_masking.list_views_containing_ig(system_name, initiator_group_id)
        if len(views) > 0:
            print '%s: In masking views %s' % (ig_name, str(views))
            sys.exit(1)
        smis_masking.delete_ig(system_name, initiator_group_id)
    elif is_remove:
        ig_hba_ids = smis_masking.list_initiators_in_ig(system_name, initiator_group_id)
        remove_ids = []
        for remove_hba in remainder:
            remove_id = smis_masking.get_hba_id(remove_hba)
            if remove_id in ig_hba_ids:
                remove_ids.append(remove_id)
            else:
                print '%s: Not found in IG' % remove_hba
        if len(remove_ids) > 0:
            print 'Removing ' + str(remove_ids) + ' from ' + ig_name
            smis_masking.remove_members_ig(system_name, initiator_group_id, remove_ids)
    elif is_add:
        add_ids = []
        for add_hba in remainder:
            try:
                add_id = smis_masking.get_hba_id(add_hba)
            except ReferenceError:
                add_id = smis_masking.create_hba_id(system_name, add_hba)
            add_ids.append(add_id)
        if len(add_ids) > 0:
            print 'Adding ' + str(add_ids) + ' to ' + ig_name
            smis_masking.add_members_ig(system_name, initiator_group_id, add_ids)
    else:
        raise AssertionError('Unknown operation')


def mod_pg():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--name', True, None, None),
                           ('--create', True, 'False', None),
                           ('--delete', True, 'False', None),
                           ('--add', True, 'False', None),
                           ('--remove', True, 'False', None)])

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    pg_name = get_paramter('--name', parameter_list)
    if use_ssl and port == 5988:
        port = 5989
    is_create = eval(get_paramter('--create', parameter_list))
    is_add = eval(get_paramter('--delete', parameter_list))
    is_remove = eval(get_paramter('--add', parameter_list))
    is_delete = eval(get_paramter('--remove', parameter_list))

    if is_add == is_remove or (is_create and is_delete):
        sys.exit(1)

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    try:
        port_group_id = smis_masking.get_pg_by_name(system_name, pg_name)
        if is_create:
            print '%s: PG already exists' % pg_name
            sys.exit(1)
    except ReferenceError:
        if is_create:
            port_group_id = smis_masking.create_pg(system_name, pg_name)
        else:
            print '%s : PG not found' % pg_name
            sys.exit(1)

    if is_delete:
        views = smis_masking.list_views_containing_pg(system_name, port_group_id)
        if len(views) > 0:
            print '%s: In masking views %s' % (pg_name, str(views))
            sys.exit(1)
        smis_masking.delete_pg(system_name, port_group_id)
    elif is_remove:
        pg_dirs = smis_masking.list_directors_in_pg(system_name, port_group_id)
        remove_dirs = []
        for remove_dir in remainder:
            if remove_dir in pg_dirs:
                remove_dirs.append(remove_dir)
            else:
                print '%s: Not found in PG' % remove_dir
        if len(remove_dirs) > 0:
            print 'Removing ' + str(remove_dirs) + ' from ' + pg_name
            smis_masking.remove_members_pg(system_name, port_group_id, remove_dirs)
    elif is_add:
        add_dirs = []
        for add_dir in remainder:
            try:
                smis_masking.get_storage_director_by_name(system_name, add_dir)
                add_dirs.append(add_dir)
            except ReferenceError:
                print '%s: director not found' % add_dir
        if len(add_dirs) > 0:
            print 'Adding ' + str(add_dirs) + ' to ' + pg_name
            smis_masking.add_members_pg(system_name, port_group_id, add_dirs)
    else:
        raise AssertionError('Unknown operation')


def mod_sg():
    parameter_list = BASE_PARAMETERS
    parameter_list.extend([('--name', True, None, None),
                           ('--create', True, 'False', None),
                           ('--delete', True, 'False', None),
                           ('--add', True, 'False', None),
                           ('--remove', True, 'False', None)])

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    sg_name = get_paramter('--name', parameter_list)
    if use_ssl and port == 5988:
        port = 5989
    is_create = eval(get_paramter('--create', parameter_list))
    is_add = eval(get_paramter('--delete', parameter_list))
    is_remove = eval(get_paramter('--add', parameter_list))
    is_delete = eval(get_paramter('--remove', parameter_list))

    if is_add == is_remove or (is_create and is_delete):
        sys.exit(1)

    smis_masking = VmaxSmisMasking(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    smis_devices = VmaxSmisDevices(smis_base=smis_masking.smis_base)
    system_name = find_symmetrix(smis_masking.smis_base, sid)

    try:
        storage_group_id = smis_masking.get_sg_by_name(system_name, sg_name)
        if is_create:
            print '%s: SG already exists' % sg_name
            sys.exit(1)
    except ReferenceError:
        if is_create:
            storage_group_id = smis_masking.create_sg(system_name, sg_name)
        else:
            print '%s : SG not found' % sg_name
            sys.exit(1)

    if is_delete:
        views = smis_masking.list_views_containing_sg(system_name, storage_group_id)
        if len(views) > 0:
            print '%s: In masking views %s' % (sg_name, str(views))
            sys.exit(1)
        smis_masking.delete_sg(system_name, storage_group_id)
    elif is_remove:
        dev_ids = smis_masking.list_volumes_in_sg(system_name, storage_group_id)
        remove_devs = []
        for remove_dev in remainder:
            while len(remove_dev) < 5:
                remove_dev = '0' + remove_dev

            if remove_dev.upper() in dev_ids:
                remove_devs.append(remove_dev.upper())
            else:
                print '%s: Not found in SG' % remove_dev.upper()
        if len(remove_devs) > 0:
            print 'Removing ' + str(remove_devs) + ' from ' + sg_name
            smis_masking.remove_members_sg(system_name, storage_group_id,
                                           smis_devices.get_volume_instance_names(system_name, remove_devs))
    elif is_add:
        add_devices = []
        for dev in remainder:
            try:
                while len(dev) < 5:
                    dev = '0' + dev

                smis_devices.get_volume_instance(system_name, dev.upper())
                add_devices.append(dev.upper())
            except ReferenceError:
                print '%s: volume not found' % dev.upper()
        if len(add_devices) > 0:
            print 'Adding ' + str(add_devices) + ' to ' + sg_name
            smis_masking.add_members_sg(system_name, storage_group_id,
                                        smis_devices.get_volume_instance_names(system_name, add_devices))
    else:
        raise AssertionError('Unknown operation')


def show_devs():
    parameter_list = BASE_PARAMETERS

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_devices = VmaxSmisDevices(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_devices.smis_base, sid)

    for dev_id in remainder:
        while len(dev_id) < 5:
            dev_id = '0' + dev_id
        dev_id = dev_id.upper()
        print dev_id + ':'
        try:
            volume_props = smis_devices.get_volume_properties(system_name, dev_id)
            for prop in sorted(volume_props.keys()):
                print '\t' + str(prop) + ' = ' + str(volume_props[prop])
        except ReferenceError:
            print '\tVolume not found.'


def show_sync():
    parameter_list = BASE_PARAMETERS

    remainder = getopt_wrapper(parameter_list)

    host = get_paramter('--host', parameter_list)
    sid = get_paramter('--sid', parameter_list)
    user = get_paramter('--user', parameter_list)
    password = get_paramter('--password', parameter_list)
    use_ssl = eval(get_paramter('--usessl', parameter_list))
    port = int(get_paramter('--port', parameter_list))
    if use_ssl and port == 5988:
        port = 5989

    smis_sync = VmaxSmisSync(host=host, port=port, user=user, passwd=password, use_ssl=use_ssl)
    system_name = find_symmetrix(smis_sync.smis_base, sid)

    for dev_id in remainder:
        while len(dev_id) < 5:
            dev_id = '0' + dev_id
        dev_id = dev_id.upper()
        print dev_id + ':'
        try:
            sync_svs = smis_sync.get_sync_sv_by_device(system_name, dev_id)
            for sync_sv in sync_svs:
                sync_props = smis_sync.get_sync_sv_properties(sync_sv)
                print '\t' + str(smis_sync.get_sync_source(sync_sv)) + ':'
                for prop in sorted(sync_props.keys()):
                    print '\t\t' + str(prop) + ' = ' + str(sync_props[prop])
        except ReferenceError:
            print '\tVolume not found.'
