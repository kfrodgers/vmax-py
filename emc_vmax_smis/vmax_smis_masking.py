# Copyright 2016 EMC Corporation

import vmax_smis_base
import time

STORAGE_GROUP_TYPE = 4
PORT_GROUP_TYPE = 3
INITIATOR_GROUP_TYPE = 2


class VmaxSmisMasking(object):
    def __init__(self, **kwargs):
        self.sg_refresh = False
        self.sg_list = None

        self.pg_refresh = False
        self.pg_list = None

        self.ig_refresh = False
        self.ig_list = None

        self.mv_refresh = False
        self.mv_list = None

        self.interval = 180
        self.refresh_time = 0

        for attr in kwargs.keys():
            setattr(self, attr, kwargs[attr])

        if not hasattr(self, 'smis_base'):
            self.smis_base = vmax_smis_base.VmaxSmisBase(**kwargs)

    def _reset(self):
        current_time = time.time()
        if (current_time > self.refresh_time) or ((current_time + self.interval) < self.refresh_time):
            self.refresh_time = current_time + self.interval
            self.sg_refresh = True
            self.pg_refresh = True
            self.ig_refresh = True
            self.mv_refresh = True

    def _list_all_mvs(self):
        self._reset()
        if self.mv_refresh or self.mv_list is None:
            self.mv_list = self.smis_base.list_masking_views()
            self.mv_refresh = False
        return self.mv_list

    def list_mv_instance_ids(self, system_name):
        groups = self._list_all_mvs()

        instance_ids = []
        for sg in groups:
            if system_name == sg['SystemName']:
                instance_ids.append(unicode(sg['DeviceID']))

        return instance_ids

    def get_mv_instance_name(self, system_name, mv_device_id):
        instance_names = self._list_all_mvs()
        for instance_name in instance_names:
            if system_name == instance_name['SystemName'] and instance_name['DeviceID'] == mv_device_id:
                break
        else:
            raise ReferenceError('%s: masking view device id not found' % mv_device_id)

        return instance_name

    def get_mv_instance(self, system_name, mv_device_id, property_list=None):
        instance_name = self.get_mv_instance_name(system_name, mv_device_id)
        return self.smis_base.get_instance(instance_name, property_list=property_list)

    def list_sgs_in_view(self, system_name, mv_device_id):
        instance_name = self.get_mv_instance_name(system_name, mv_device_id)
        return self.smis_base.list_storage_group_in_view(instance_name)

    def list_pgs_in_view(self, system_name, mv_device_id):
        instance_name = self.get_mv_instance_name(system_name, mv_device_id)
        return self.smis_base.list_port_group_in_view(instance_name)

    def list_igs_in_view(self, system_name, mv_device_id):
        instance_name = self.get_mv_instance_name(system_name, mv_device_id)
        return self.smis_base.list_initiator_group_in_view(instance_name)

    def list_initiators_in_view(self, system_name, mv_device_id):
        instance_name = self.get_mv_instance_name(system_name, mv_device_id)
        return self.smis_base.find_initiators_in_group(instance_name)

    def create_masking_view(self, system_name, masking_view_name, initiator_masking_group,
                            device_masking_group, target_masking_group):
        rc, job = self.smis_base.invoke_controller_method('CreateMaskingView', system_name,
                                                          ElementName=masking_view_name,
                                                          InitiatorMaskingGroup=initiator_masking_group,
                                                          DeviceMaskingGroup=device_masking_group,
                                                          TargetMaskingGroup=target_masking_group)
        return rc, job

    def _list_all_sgs(self):
        self._reset()
        if self.sg_refresh or self.sg_list is None:
            self.sg_list = self.smis_base.list_storage_group_names()
            self.sg_refresh = False
        return self.sg_list

    def list_sg_instance_ids(self, system_name):
        groups = self._list_all_sgs()

        instance_ids = []
        for sg in groups:
            if system_name in sg['InstanceID']:
                instance_ids.append(unicode(sg['InstanceID']))

        return instance_ids

    def get_sg_name(self, system_name, sg_instance_id):
        sg_instance = self.get_sg_instance(system_name, sg_instance_id, property_list=['ElementName'])
        return sg_instance['ElementName']

    def get_sg_instance_name(self, system_name, sg_instance_id):
        instance_names = self._list_all_sgs()
        for instance_name in instance_names:
            if system_name in instance_name['InstanceID'] and instance_name['InstanceID'] == sg_instance_id:
                break
        else:
            raise ReferenceError('%s: storage group instance id not found' % sg_instance_id)

        return instance_name

    def get_sg_by_name(self, system_name, storage_group_name):
        for sg in self.smis_base.list_storage_groups(property_list=['ElementName', 'InstanceID']):
            if system_name in sg['InstanceID'] and sg['ElementName'] == storage_group_name:
                break
        else:
            raise ReferenceError('%s - %s: storage group not found' % (system_name, storage_group_name))

        return sg['InstanceID']

    def get_sg_instance(self, system_name, sg_instance_id, property_list=None):
        instance_name = self.get_sg_instance_name(system_name, sg_instance_id)
        return self.smis_base.get_instance(instance_name, property_list=property_list)

    def check_storage_group(self, system_name, sg_instance_id):
        return self.get_sg_instance_name(system_name, sg_instance_id) is not None

    def list_volumes_in_sg(self, system_name, sg_instance_id):
        return self.smis_base.list_volumes_in_group(self.get_sg_instance_name(system_name, sg_instance_id))

    def list_views_containing_sg(self, system_name, sg_instance_id):
        instances = self.smis_base.list_views_for_storage_group(self.get_sg_instance_name(system_name, sg_instance_id))
        mv_device_ids = []
        for instance in instances:
            mv_device_ids.append(instance['DeviceID'])
        return mv_device_ids

    def create_sg(self, system_name, sg_name):
        rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=sg_name,
                                                          Type=self.smis_base.get_ecom_int(STORAGE_GROUP_TYPE, '16'),
                                                          DeleteWhenBecomesUnassociated=False)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: create failed %(rc)lu, %(error)s." % \
                                    {'name': sg_name,
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        self.sg_refresh = True

        sg_instance_id = None
        if 'MaskingGroup' in job and 'InstanceID' in job['MaskingGroup']:
            sg_instance_id = job['MaskingGroup']['InstanceID']

        return sg_instance_id

    def add_members_sg(self, system_name, sg_instance_id, volume_instances):
        instance_name = self.get_sg_instance_name(system_name, sg_instance_id)
        rc, job = self.smis_base.invoke_controller_method('AddMembers', system_name, MaskingGroup=instance_name,
                                                          Members=volume_instances)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: add members to SG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def remove_members_sg(self, system_name, sg_instance_id, volume_instances):
        instance_name = self.get_sg_instance_name(system_name, sg_instance_id)
        rc, job = self.smis_base.invoke_controller_method('RemoveMembers', system_name, MaskingGroup=instance_name,
                                                          Members=volume_instances)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: remove members from SG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def delete_sg(self, system_name, sg_instance_id, force=True):
        instance_name = self.get_sg_instance_name(system_name, sg_instance_id)
        rc, job = self.smis_base.invoke_controller_method('DeleteGroup', system_name,
                                                          MaskingGroup=instance_name, Force=force)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: delete failed %(rc)lu, %(error)s." % \
                                    {'name': str(sg_instance_id),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)
        return rc

    def list_storage_directors(self, system_name):
        directors = []
        endpoints = self.smis_base.list_storage_endpoints(system_name)
        for e in endpoints:
            if e['CreationClassName'] == u'Symm_FCSCSIProtocolEndpoint' or \
                    e['CreationClassName'] == u'Symm_iSCSIProtocolEndpoint' or \
                    e['CreationClassName'] == u'Symm_VirtualiSCSIProtocolEndpoint':
                directors.append(e)
        return directors

    def _list_all_pgs(self):
        self._reset()
        if self.pg_refresh or self.pg_list is None:
            self.pg_list = self.smis_base.list_port_groups()
            self.pg_refresh = False
        return self.pg_list

    def list_pg_instance_ids(self, system_name):
        groups = self._list_all_pgs()

        instance_ids = []
        for pg in groups:
            if system_name in pg['InstanceID']:
                instance_ids.append(pg['InstanceID'])

        return instance_ids

    def get_pg_name(self, system_name, pg_instance_id):
        pg_instance = self.get_pg_instance(system_name, pg_instance_id)
        return pg_instance['ElementName']

    def get_pg_instance_name(self, system_name, pg_instance_id):
        instance_names = self._list_all_pgs()
        for instance_name in instance_names:
            if system_name in instance_name['InstanceID'] and instance_name['InstanceID'] == pg_instance_id:
                break
        else:
            raise ReferenceError('%s: port group instance id not found' % pg_instance_id)

        return instance_name

    def get_pg_instance(self, system_name, pg_instance_id):
        instance_name = self.get_pg_instance_name(system_name, pg_instance_id)
        return self.smis_base.get_instance(instance_name)

    def check_port_group(self, system_name, pg_instance_id):
        return self.get_pg_instance_name(system_name, pg_instance_id) is not None

    def list_directors_in_pg(self, system_name, pg_instance_id):
        return self.smis_base.list_ports_in_group(self.get_pg_instance_name(system_name, pg_instance_id))

    def list_views_containing_pg(self, system_name, pg_instance_id):
        return self.smis_base.list_views_for_port_group(self.get_pg_instance_name(system_name, pg_instance_id))

    def create_pg(self, system_name, pg_name, director_names=None):
        if director_names is not None and len(director_names) > 0:
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=pg_name,
                                                              Type=self.smis_base.get_ecom_int(PORT_GROUP_TYPE, '16'),
                                                              Members=director_names)
        else:
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=pg_name,
                                                              Type=self.smis_base.get_ecom_int(PORT_GROUP_TYPE, '16'))
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: create PG failed %(rc)lu, %(error)s." % \
                                    {'name': pg_name,
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        self.pg_refresh = True

        pg_instance_id = None
        if 'MaskingGroup' in job and 'InstanceID' in job['MaskingGroup']:
            pg_instance_id = job['MaskingGroup']['InstanceID']

        return pg_instance_id

    def add_members_pg(self, system_name, pg_instance_id, director_names):
        instance_name = self.get_pg_instance_name(system_name, pg_instance_id)
        rc, job = self.smis_base.invoke_controller_method('AddMembers', system_name, MaskingGroup=instance_name,
                                                          Members=director_names)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: add members to PG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def remove_members_pg(self, system_name, pg_instance_id, director_names):
        instance_name = self.get_pg_instance_name(system_name, pg_instance_id)
        rc, job = self.smis_base.invoke_controller_method('RemoveMembers', system_name, MaskingGroup=instance_name,
                                                          Members=director_names)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: remove members from PG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def delete_pg(self, system_name, pg_instance_id, force=True):
        instance_name = self.get_pg_instance_name(system_name, pg_instance_id)
        rc, job = self.smis_base.invoke_controller_method('DeleteGroup', system_name,
                                                          MaskingGroup=instance_name, Force=force)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: delete failed %(rc)lu, %(error)s." % \
                                    {'name': str(pg_instance_id),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)
        return rc

    def _list_all_igs(self):
        self._reset()
        if self.ig_refresh or self.sg_list is None:
            self.ig_list = self.smis_base.list_initiator_groups()
            self.ig_refresh = False
        return self.ig_list

    def list_ig_instance_ids(self, system_name):
        groups = self._list_all_igs()

        instance_ids = []
        for ig in groups:
            if system_name in ig['InstanceID']:
                instance_ids.append(unicode(ig['InstanceID']))

        return instance_ids

    def get_ig_name(self, system_name, ig_instance_id):
        ig_instance = self.get_ig_instance(system_name, ig_instance_id)
        return ig_instance['ElementName']

    def get_ig_instance_name(self, system_name, ig_instance_id):
        instance_names = self._list_all_igs()
        for instance_name in instance_names:
            if system_name in instance_name['InstanceID'] and instance_name['InstanceID'] == ig_instance_id:
                break
        else:
            raise ReferenceError('%s: storage group instance id not found' % ig_instance_id)

        return instance_name

    def get_ig_instance(self, system_name, ig_instance_id):
        instance_name = self.get_ig_instance_name(system_name, ig_instance_id)
        return self.smis_base.get_instance(instance_name)

    def check_initiator_group(self, system_name, ig_instance_id):
        return self.get_sg_instance_name(system_name, ig_instance_id) is not None

    def list_initiators_in_ig(self, system_name, ig_instance_id):
        return self.smis_base.find_initiators_in_group(self.get_ig_instance_name(system_name, ig_instance_id))

    def list_views_containing_ig(self, system_name, ig_instance_id):
        return self.smis_base.list_views_for_initiator_group(self.get_ig_instance_name(system_name, ig_instance_id))

    def _storage_hardware_type(self, www_or_iqn):
        type_id = 0
        try:
            int(www_or_iqn, 16)
            type_id = 2
        except Exception:
            if 'iqn' in www_or_iqn.lower():
                type_id = 5
        if type_id == 0:
            raise RuntimeError("Cannot determine the hardware type.")
        return self.smis_base.get_ecom_int(type_id, '16')

    def create_storage_hardware_id(self, system_name, wwn_or_iqn):

        config_service = self.smis_base.find_storage_hardwareid_service(system_name)
        rc, job = self.smis_base.invoke_method('CreateStorageHardwareID', config_service,
                                               StorageID=wwn_or_iqn, IDType=self._storage_hardware_type(wwn_or_iqn))
        if 'HardwareID' in job:
            hardware_id_list = job['HardwareID']
        else:
            message = "CreateStorageHardwareID failed. initiator: %(initiator)s, rc=%(rc)d, job=%(job)s." % \
                      {'initiator': wwn_or_iqn, 'rc': rc, 'job': unicode(job)}
            raise RuntimeError(message)
        return hardware_id_list

    def delete_storage_hardware_id(self, system_name, hardware_instance):
        config_service = self.smis_base.find_storage_hardwareid_service(system_name)
        rc, job = self.smis_base.invoke_method('DeleteStorageHardwareID', config_service,
                                               HardwareID=hardware_instance)
        if rc != 0:
            message = "%(name)s: delete hardware id failed %(rc)lu, %(error)s." % \
                      {'name': str(hardware_instance), 'rc': rc, 'error': job['ErrorDescription']}
            raise RuntimeError(message)
        return rc

    def list_storage_hardware(self):
        hardware_instances = self.smis_base.list_all_initiators()
        hardware_names = []
        for instance in hardware_instances:
            hardware_names.append(instance['ElementName'])
        return hardware_names

    def get_storage_hardware_instance(self, hardware_name):
        hardware_instances = self.smis_base.list_all_initiators()
        hardware_names = []
        for instance in hardware_instances:
            if hardware_name == instance['ElementName']:
                break
        else:
            raise ReferenceError('%s: storage hardware not found' % hardware_name)

        return instance

    def create_ig(self, system_name, ig_name, hardware_names=None):
        if hardware_names is not None and len(hardware_names) > 0:
            initiator_names = []
            for name in hardware_names:
                initiator_names.append(self.get_storage_hardware_instance(name))

            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=ig_name,
                                                              Type=self.smis_base.get_ecom_int(INITIATOR_GROUP_TYPE, '16'),
                                                              Members=initiator_names)
        else:
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=ig_name,
                                                              Type=self.smis_base.get_ecom_int(INITIATOR_GROUP_TYPE, '16'))
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: create IG failed %(rc)lu, %(error)s." % \
                                    {'name': ig_name,
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        self.ig_refresh = True

        ig_instance_id = None
        if 'MaskingGroup' in job and 'InstanceID' in job['MaskingGroup']:
            ig_instance_id = job['MaskingGroup']['InstanceID']

        return ig_instance_id

    def add_members_ig(self, system_name, ig_instance_id, initiator_names):
        instance_name = self.get_ig_instance_name(system_name, ig_instance_id)
        rc, job = self.smis_base.invoke_controller_method('AddMembers', system_name, MaskingGroup=instance_name,
                                                          Members=initiator_names)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: add members to IG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def remove_members_ig(self, system_name, ig_instance_id, initiator_names):
        instance_name = self.get_ig_instance_name(system_name, ig_instance_id)
        rc, job = self.smis_base.invoke_controller_method('RemoveMembers', system_name, MaskingGroup=instance_name,
                                                          Members=initiator_names)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: remove members from IG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def delete_ig(self, system_name, ig_instance_id, force=True):
        instance_name = self.get_ig_instance_name(system_name, ig_instance_id)
        rc, job = self.smis_base.invoke_controller_method('DeleteGroup', system_name,
                                                          MaskingGroup=instance_name, Force=force)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: delete IG failed %(rc)lu, %(error)s." % \
                                    {'name': str(ig_instance_id),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)
        return rc