# Copyright 2016 EMC Corporation

import vmax_smis_base

STORAGEGROUPTYPE = 4
PORTGROUPTYPE = 3


class VmaxSmisMasking(object):
    def __init__(self, **kwargs):
        self.sg_refresh = False
        self.sg_list = None

        self.pg_refresh = False
        self.pg_list = None

        for attr in kwargs.keys():
            setattr(self, attr, kwargs[attr])

        if not hasattr(self, 'smis_base'):
            self.smis_base = vmax_smis_base.VmaxSmisBase(**kwargs)

    def create_masking_view(self, system_name, masking_view_name, initiator_masking_group,
                            device_masking_group, target_masking_group):
        rc, job = self.smis_base.invoke_method('CreateMaskingView', system_name, ElementName=masking_view_name,
                                               InitiatorMaskingGroup=initiator_masking_group,
                                               DeviceMaskingGroup=device_masking_group,
                                               TargetMaskingGroup=target_masking_group)
        return rc, job

    def _list_all_sgs(self):
        if self.sg_refresh or self.sg_list is None:
            self.sg_list = self.smis_base.list_storage_groups()
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
        sg_instance = self.get_sg_instance(system_name, sg_instance_id)
        return sg_instance['ElementName']

    def get_sg_instance_name(self, system_name, sg_instance_id):
        instance_names = self._list_all_sgs()
        for instance_name in instance_names:
            if system_name in instance_name['InstanceID'] and instance_name['InstanceID'] == sg_instance_id:
                break
        else:
            raise ReferenceError('%s: storage group instance id not found' % sg_instance_id)

        return instance_name

    def get_sg_instance(self, system_name, sg_instance_id):
        instance_name = self.get_sg_instance_name(system_name, sg_instance_id)
        return self.smis_base.get_instance(instance_name)

    def check_storage_group(self, system_name, sg_instance_id):
        return self.get_sg_instance_name(system_name, sg_instance_id) is not None

    def list_volumes_in_sg(self, system_name, sg_instance_id):
        return self.smis_base.list_volumes_in_group(self.get_sg_instance_name(system_name, sg_instance_id))

    def list_views_containing_sg(self, system_name, sg_instance_id):
        return self.smis_base.list_views_for_storage_group(self.get_sg_instance_name(system_name, sg_instance_id))

    def create_sg(self, system_name, sg_name):
        rc, job = self.smis_base.invoke_method('CreateGroup', system_name, GroupName=sg_name,
                                               Type=self.smis_base.get_ecom_int(STORAGEGROUPTYPE, '16'),
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

    def delete_sg(self, system_name, sg_instance_id):
        instance_name = self.get_sg_instance_name(system_name, sg_instance_id)
        rc, job = self.smis_base.invoke_method('DeleteGroup', system_name,
                                               MaskingGroup=instance_name, Force=True)
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
        endpoints = self.smis_base.list_storage_enpoints()
        for e in endpoints:
            if system_name in e['SystemName']:
                directors.append(e)
        return directors

    def _list_all_pgs(self):
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

    def create_pg(self, system_name, pg_name, director_names):
        rc, job = self.smis_base.invoke_method('CreateGroup', system_name, GroupName=pg_name,
                                               Type=self.smis_base.get_ecom_int(PORTGROUPTYPE, '16'),
                                               Members=director_names)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: create failed %(rc)lu, %(error)s." % \
                                    {'name': pg_name,
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)

        self.pg_refresh = True

        pg_instance_id = None
        if 'MaskingGroup' in job and 'InstanceID' in job['MaskingGroup']:
            pg_instance_id = job['MaskingGroup']['InstanceID']

        return pg_instance_id

    def delete_pg(self, system_name, pg_instance_id):
        instance_name = self.get_pg_instance_name(system_name, pg_instance_id)
        rc, job = self.smis_base.invoke_method('DeleteGroup', system_name,
                                               MaskingGroup=instance_name, Force=True)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "%(name)s: delete failed %(rc)lu, %(error)s." % \
                                    {'name': str(pg_instance_id),
                                     'rc': rc,
                                     'error': errordesc}
                raise RuntimeError(exception_message)
        return rc
