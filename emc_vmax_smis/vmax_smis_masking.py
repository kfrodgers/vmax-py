# Copyright 2016 EMC Corporation

from vmax_smis_base import VmaxSmisBase, get_ecom_int
import time

STORAGE_GROUP_TYPE = 4
PORT_GROUP_TYPE = 3
INITIATOR_GROUP_TYPE = 2

HBA_TYPE_WWN = 2
HBA_TYPE_IQN = 5


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
            self.smis_base = VmaxSmisBase(**kwargs)

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
                instance_ids.append(sg['DeviceID'])

        return instance_ids

    def get_mv_instance_name(self, system_name, mv_device_id):
        mv_instance = self.get_mv_instance(system_name, mv_device_id)
        return mv_instance.path

    def get_mv_instance(self, system_name, mv_device_id):
        mv_instances = self._list_all_mvs()
        for mv_instance in mv_instances:
            if system_name == mv_instance['SystemName'] and mv_instance['DeviceID'] == mv_device_id:
                break
        else:
            raise ReferenceError('%s: masking view device id not found' % mv_device_id)

        return mv_instance

    def list_sgs_in_view(self, system_name, mv_device_id):
        sg_ids = []
        sg_names = self.smis_base.list_storage_group_in_view(self.get_mv_instance_name(system_name, mv_device_id))
        for sg_name in sg_names:
            sg_ids.append(sg_name['InstanceID'])

        return sg_ids

    def list_pgs_in_view(self, system_name, mv_device_id):
        pg_ids = []
        pg_names = self.smis_base.list_port_group_in_view(self.get_mv_instance_name(system_name, mv_device_id))
        for pg in pg_names:
            pg_ids.append(pg['InstanceID'])

        return pg_ids

    def list_igs_in_view(self, system_name, mv_device_id):
        ig_ids = []
        ig_names = self.smis_base.list_initiator_group_in_view(self.get_mv_instance_name(system_name, mv_device_id))
        for ig in ig_names:
            ig_ids.append(ig['InstanceID'])

        return ig_ids

    def list_initiators_in_view(self, system_name, mv_device_id):
        initiator_ids = []
        initiator_names = self.smis_base.find_initiators_in_group(self.get_mv_instance_name(system_name, mv_device_id))
        for names in initiator_names:
            initiator_ids.append(names['InstanceID'])

        return initiator_ids

    def create_masking_view(self, system_name, mv_name, ig_name, sg_name, pg_name):
        ig_instance_name = self.get_ig_instance_name(system_name, self.get_ig_by_name(system_name, ig_name))
        sg_instance_name = self.get_sg_instance_name(system_name, self.get_sg_by_name(system_name, sg_name))
        pg_instance_name = self.get_pg_instance_name(system_name, self.get_pg_by_name(system_name, pg_name))
        rc, job = self.smis_base.invoke_controller_method('CreateMaskingView', system_name,
                                                          ElementName=mv_name,
                                                          InitiatorMaskingGroup=ig_instance_name,
                                                          DeviceMaskingGroup=sg_instance_name,
                                                          TargetMaskingGroup=pg_instance_name)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: CreateMaskingView failed %(rc)lu, %(error)s." % \
                                    {'name': mv_name,
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        self.mv_refresh = True

        mv_instance_id = None
        if 'MaskingGroup' in job and 'InstanceID' in job['MaskingGroup']:
            mv_instance_id = job['MaskingGroup']['InstanceID']

        return mv_instance_id

    def delete_masking_view(self, system_name, mv_instance_id, force=True):
        instance_name = self.get_mv_instance_name(system_name, mv_instance_id)
        rc, job = self.smis_base.invoke_controller_method('DeleteMaskingView', system_name,
                                                          ProtocolController=instance_name, Force=force)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: DeleteMaskingView failed, %(rc)lu, %(error)s." % \
                                    {'name': str(mv_instance_id),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)
        return rc

    def _list_all_sgs(self):
        self._reset()
        if self.sg_refresh or self.sg_list is None:
            self.sg_list = self.smis_base.list_storage_groups()
            self.sg_refresh = False
        return self.sg_list

    def list_sg_instance_ids(self, system_name):
        sg_instances = self._list_all_sgs()

        instance_ids = []
        for sg in sg_instances:
            if system_name in sg['InstanceID']:
                instance_ids.append(sg['InstanceID'])

        return instance_ids

    def get_sg_name(self, system_name, sg_instance_id):
        sg_instance = self.get_sg_instance(system_name, sg_instance_id)
        return sg_instance['ElementName']

    def get_sg_by_name(self, system_name, storage_group_name):
        sg_instances = self._list_all_sgs()
        for sg in sg_instances:
            if system_name in sg['InstanceID'] and sg['ElementName'] == storage_group_name:
                break
        else:
            raise ReferenceError('%s - %s: storage group not found' % (system_name, storage_group_name))

        return sg['InstanceID']

    def get_sg_instance(self, system_name, sg_instance_id):
        sg_instances = self._list_all_sgs()
        for sg_instance in sg_instances:
            if system_name in sg_instance['InstanceID'] and sg_instance['InstanceID'] == sg_instance_id:
                break
        else:
            raise ReferenceError('%s: storage group instance id not found' % sg_instance_id)

        return sg_instance

    def get_sg_instance_name(self, system_name, sg_instance_id):
        sg_instance = self.get_sg_instance(system_name, sg_instance_id)
        return sg_instance.path

    def list_volumes_in_sg(self, system_name, sg_instance_id):
        device_ids = []
        volumes = self.smis_base.list_volumes_in_group(self.get_sg_instance_name(system_name, sg_instance_id))
        for volume in volumes:
            device_ids.append(volume['DeviceID'])

        return device_ids

    def list_views_containing_sg(self, system_name, sg_instance_id):
        instances = self.smis_base.list_views_for_storage_group(self.get_sg_instance_name(system_name, sg_instance_id))
        mv_device_ids = []
        for instance in instances:
            mv_device_ids.append(instance['DeviceID'])
        return mv_device_ids

    def create_sg(self, system_name, sg_name, volume_instances=None):
        if volume_instances is not None and len(volume_instances) > 0:
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=sg_name,
                                                              Type=get_ecom_int(STORAGE_GROUP_TYPE, '16'),
                                                              Members=volume_instances,
                                                              DeleteWhenBecomesUnassociated=False)
        else:
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=sg_name,
                                                              Type=get_ecom_int(STORAGE_GROUP_TYPE, '16'),
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
                directors.append(e['SystemName'])
        return directors

    def get_storage_director_by_name(self, system_name, dir_name):
        endpoints = self.smis_base.list_storage_endpoints(system_name)
        for endpoint in endpoints:
            if (endpoint['CreationClassName'] == u'Symm_FCSCSIProtocolEndpoint' or
                    endpoint['CreationClassName'] == u'Symm_iSCSIProtocolEndpoint' or
                    endpoint['CreationClassName'] == u'Symm_VirtualiSCSIProtocolEndpoint') and \
                    endpoint['SystemName'] == dir_name:
                break
        else:
            raise ReferenceError('%s: director not found' % dir_name)

        return endpoint

    def get_storage_directors(self, system_name, director_names):
        endpoints = []
        for name in director_names:
            endpoints.append(self.get_storage_director_by_name(system_name, name))

        return endpoints

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

    def get_pg_by_name(self, system_name, pg_name):
        pg_instances = self._list_all_pgs()
        for instance in pg_instances:
            if system_name in instance['InstanceID'] and instance['ElementName'] == pg_name:
                break
        else:
            raise ReferenceError('%s: port group instance id not found' % pg_name)

        return instance['InstanceID']

    def get_pg_instance_name(self, system_name, pg_instance_id):
        pg_instance = self.get_pg_instance(system_name, pg_instance_id)
        return pg_instance.path

    def get_pg_instance(self, system_name, pg_instance_id):
        pg_instances = self._list_all_pgs()
        for instance in pg_instances:
            if system_name in instance['InstanceID'] and instance['InstanceID'] == pg_instance_id:
                break
        else:
            raise ReferenceError('%s: port group instance id not found' % pg_instance_id)

        return instance

    def list_directors_in_pg(self, system_name, pg_instance_id):
        dir_names = []
        endpoints = self.smis_base.list_ports_in_group(self.get_pg_instance_name(system_name, pg_instance_id))
        for endpoint in endpoints:
            dir_names.append(endpoint['SystemName'])

        return dir_names

    def list_views_containing_pg(self, system_name, pg_instance_id):
        instances = self.smis_base.list_views_for_port_group(self.get_pg_instance_name(system_name, pg_instance_id))
        mv_device_ids = []
        for instance in instances:
            mv_device_ids.append(instance['DeviceID'])
        return mv_device_ids

    def create_pg(self, system_name, pg_name, director_names=None):
        if director_names is not None and len(director_names) > 0:
            members = self.get_storage_directors(system_name, director_names)
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=pg_name,
                                                              Type=get_ecom_int(PORT_GROUP_TYPE, '16'),
                                                              Members=members)
        else:
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=pg_name,
                                                              Type=get_ecom_int(PORT_GROUP_TYPE, '16'))
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
        members = self.get_storage_directors(system_name, director_names)
        rc, job = self.smis_base.invoke_controller_method('AddMembers', system_name, MaskingGroup=instance_name,
                                                          Members=members)
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
        members = self.get_storage_directors(system_name, director_names)
        rc, job = self.smis_base.invoke_controller_method('RemoveMembers', system_name, MaskingGroup=instance_name,
                                                          Members=members)
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
                instance_ids.append(ig['InstanceID'])

        return instance_ids

    def get_ig_name(self, system_name, ig_instance_id):
        ig_instance = self.get_ig_instance(system_name, ig_instance_id)
        return ig_instance['ElementName']

    def get_ig_by_name(self, system_name, ig_name):
        instance_names = self._list_all_igs()
        for instance in instance_names:
            if system_name in instance['InstanceID'] and instance['ElementName'] == ig_name:
                break
        else:
            raise ReferenceError('%s: storage group instance id not found' % ig_name)

        return instance['InstanceID']

    def get_ig_instance_name(self, system_name, ig_instance_id):
        instance = self.get_ig_instance(system_name, ig_instance_id)
        return instance.path

    def get_ig_instance(self, system_name, ig_instance_id):
        instances = self._list_all_igs()
        for instance in instances:
            if system_name in instance['InstanceID'] and instance['InstanceID'] == ig_instance_id:
                break
        else:
            raise ReferenceError('%s: IG instance id not found' % ig_instance_id)

        return instance

    def list_initiators_in_ig(self, system_name, ig_instance_id):
        hba_ids = []
        initiators = self.smis_base.find_initiators_in_group(self.get_ig_instance_name(system_name, ig_instance_id))
        for initiator in initiators:
            hba_ids.append(initiator['InstanceID'])

        return hba_ids

    def list_views_containing_ig(self, system_name, ig_instance_id):
        instances = self.smis_base.list_views_for_initiator_group(self.get_ig_instance_name(system_name,
                                                                                            ig_instance_id))
        mv_device_ids = []
        for instance in instances:
            mv_device_ids.append(instance['DeviceID'])
        return mv_device_ids

    @staticmethod
    def get_hba_type(www_or_iqn):
        type_id = 0
        try:
            int(www_or_iqn, 16)
            if len(www_or_iqn) == 16:
                type_id = HBA_TYPE_WWN
        except ValueError:
            if www_or_iqn.lower().startswith('iqn'):
                type_id = HBA_TYPE_IQN
        if type_id == 0:
            raise RuntimeError("%s: Invalid format for WWW or IQN." % www_or_iqn)
        return type_id

    def create_hba_id(self, system_name, wwn_or_iqn):
        config_service = self.smis_base.find_storage_hardwareid_service(system_name)
        rc, job = self.smis_base.invoke_method('CreateStorageHardwareID', config_service,
                                               StorageID=wwn_or_iqn,
                                               IDType=get_ecom_int(self.get_hba_type(wwn_or_iqn), '16'))
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                message = "CreateStorageHardwareID failed. initiator: %(initiator)s, rc=%(rc)d, job=%(job)s." % \
                          {'initiator': wwn_or_iqn, 'rc': rc, 'job': unicode(job)}
                raise RuntimeError(message)

        hba_id = None
        if 'HardwareID' in job:
            hba_id = job['HardwareID']['InstanceID']

        return hba_id

    def delete_hba_id(self, system_name, hba_id):
        config_service = self.smis_base.find_storage_hardwareid_service(system_name)
        rc, job = self.smis_base.invoke_method('DeleteStorageHardwareID', config_service,
                                               HardwareID=self.get_hba_instance_name(hba_id))
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                message = "%(name)s: DeleteStorageHardwareID failed %(rc)lu, %(error)s." % \
                          {'name': str(hba_id), 'rc': rc, 'error': job['ErrorDescription']}
                raise RuntimeError(message)
        return rc

    def list_hba_ids(self):
        hardware_instances = self.smis_base.list_all_initiators()
        hardware_names = []
        for instance in hardware_instances:
            hardware_names.append(instance['InstanceID'])
        return hardware_names

    def get_hba_id(self, hardware_name):
        hardware_instances = self.smis_base.list_all_initiators()
        for instance in hardware_instances:
            if hardware_name == instance['ElementName']:
                break
        else:
            raise ReferenceError('%s: storage hardware not found' % hardware_name)

        return instance['InstanceID']

    def get_hba_instance_name(self, hba_id):
        hardware_instances = self.smis_base.list_all_initiators()
        for instance in hardware_instances:
            if hba_id == instance['InstanceID']:
                break
        else:
            raise ReferenceError('%s: storage hardware not found' % hba_id)

        return instance.path

    def get_hba_instance_names(self, hba_ids):
        hba_names = []
        for hba_id in hba_ids:
            hba_names.append(self.get_hba_instance_name(hba_id))
        return hba_names

    def create_ig(self, system_name, ig_name, hba_ids=None):
        if hba_ids is not None and len(hba_ids) > 0:
            ecom_type = get_ecom_int(INITIATOR_GROUP_TYPE, '16')
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=ig_name,
                                                              Type=ecom_type,
                                                              Members=self.get_hba_instance_names(hba_ids))
        else:
            ecom_type = get_ecom_int(INITIATOR_GROUP_TYPE, '16')
            rc, job = self.smis_base.invoke_controller_method('CreateGroup', system_name, GroupName=ig_name,
                                                              Type=ecom_type)
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

    def add_members_ig(self, system_name, ig_instance_id, hba_ids):
        instance_name = self.get_ig_instance_name(system_name, ig_instance_id)
        rc, job = self.smis_base.invoke_controller_method('AddMembers', system_name, MaskingGroup=instance_name,
                                                          Members=self.get_hba_instance_names(hba_ids))
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: add members to IG failed %(rc)lu, %(error)s." % \
                                    {'name': str(instance_name),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        return rc

    def remove_members_ig(self, system_name, ig_instance_id, hba_ids):
        instance_name = self.get_ig_instance_name(system_name, ig_instance_id)
        rc, job = self.smis_base.invoke_controller_method('RemoveMembers', system_name, MaskingGroup=instance_name,
                                                          Members=self.get_hba_instance_names(hba_ids))
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
