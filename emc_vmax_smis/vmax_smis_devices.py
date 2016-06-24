# Copyright 2016 EMC Corporation

import time
from vmax_smis_base import VmaxSmisBase

THINPROVISIONINGCOMPOSITE = 32768
THINPROVISIONING = 5


class VmaxSmisDevices(object):
    def __init__(self, **kwargs):
        self.devices_refresh = False
        self.devices = None

        self.interval = 300
        self.refresh_time = 0

        for attr in kwargs.keys():
            setattr(self, attr, kwargs[attr])

        if not hasattr(self, 'smis_base'):
            self.smis_base = VmaxSmisBase(**kwargs)

    def _reset(self):
        current_time = time.time()
        if (current_time > self.refresh_time) or ((current_time + self.interval) < self.refresh_time):
            self.refresh_time = current_time + self.interval
            self.devices_refresh = True

    def _load_all_devices(self):
        if self.devices_refresh or self.devices is None:
            self.devices = self.smis_base.list_storage_volumes_names()
            self.devices_refresh = False

        return self.devices

    def get_volume_instance(self, system_name, device_id):
        for volume in self._load_all_devices():
            if volume['SystemName'] == system_name and volume['DeviceID'] == device_id:
                break
        else:
            raise ReferenceError('%s - %s: volume not found' % (system_name, device_id))

        return volume

    def get_volume_by_name(self, system_name, volume_name):
        for volume in self.smis_base.list_storage_volumes(property_list=['ElementName', 'SystemName', 'DeviceID']):
            if volume['SystemName'] == system_name and volume['ElementName'] == unicode(volume_name):
                break
        else:
            raise ReferenceError('%s - %s: volume not found' % (system_name, volume_name))

        return self.get_volume_instance(system_name, volume['DeviceID'])

    def list_all_devices(self, system_name):
        devices = []
        for o in self._load_all_devices():
            if o['SystemName'] == system_name:
                devices.append(str(o['DeviceID']))
        return devices

    def get_space_consumed(self, system_name, device_id):
        volume = self.get_volume_instance(system_name, device_id)

        space_consumed = -1L
        unit_names = self.smis_base.get_unit_names(volume)
        for unit_name in unit_names:
            properties_list = unit_name.properties.items()
            for properties in properties_list:
                if properties[0] == 'SpaceConsumed':
                    cim_properties = properties[1]
                    space_consumed = long(cim_properties.value)
                    break
            if space_consumed >= 0L:
                break

        return space_consumed

    def get_extended_volume(self, system_name, device_id, property_list=None):
        return self.smis_base.get_instance(self.get_volume_instance(system_name, device_id),
                                           property_list=property_list)

    def get_volume_size(self, system_name, device_id):
        extended_volume = self.get_extended_volume(system_name, device_id,
                                                   property_list=['ConsumableBlocks', 'BlockSize'])

        block_size = 0L
        num_blocks = 0L
        properties_list = extended_volume.properties.items()
        for properties in properties_list:
            if properties[0] == 'ConsumableBlocks':
                cim_properties = properties[1]
                num_blocks = long(cim_properties.value)
            if properties[0] == 'BlockSize':
                cim_properties = properties[1]
                block_size = long(cim_properties.value)
            if block_size > 0 and num_blocks > 0:
                break

        return num_blocks * block_size

    def get_volume_properties(self, system_name, device_id, property_list=None):
        extended_volume = self.get_extended_volume(system_name, device_id, property_list=property_list)

        properties = {}

        properties_list = extended_volume.properties.items()
        for p in properties_list:
            if property_list is None or len(property_list) == 0:
                cim_properties = p[1]
                properties[p[0]] = cim_properties.value
            else:
                for req in property_list:
                    if req == p[0]:
                        cim_properties = p[1]
                        properties[p[0]] = cim_properties.value
                        break

        return properties

    def _list_pool_instance_names(self, system_name):
        system_instance_name = self.smis_base.find_storage_system(system_name)
        if self.smis_base.is_array_v3(system_name):
            pool_instance_names = self.smis_base.find_srp_storage_pool(system_instance_name)
        else:
            pool_instance_names = self.smis_base.find_virtual_provisioning_pool(system_instance_name)

        return pool_instance_names

    def _find_pool_instance_name(self, system_name, pool_instance_id):
        pool_instance_names = self._list_pool_instance_names(system_name)
        for name in pool_instance_names:
            if name['InstanceID'] == pool_instance_id:
                break
        else:
            raise ReferenceError('%s: pool instance not found' % pool_instance_id)

        return name

    def list_storage_pools(self, system_name):
        pool_instance_names = self._list_pool_instance_names(system_name)
        pool_instance_ids = []
        for name in pool_instance_names:
            pool_instance_ids.append(name['InstanceID'])

        return pool_instance_ids

    def get_storage_group(self, system_name, device_id):
        instances = self.smis_base.list_storage_groups_from_volume(self.get_volume_instance(system_name, device_id))
        groups = []
        for i in instances:
            groups.append(i['InstanceID'])
        return groups

    def create_volume(self, system_name, volume_name, pool_instance_id, volume_size):
        pool_instance_name = self._find_pool_instance_name(system_name, pool_instance_id)
        rc, job = self.smis_base.invoke_storage_method('CreateOrModifyElementFromStoragePool', system_name,
                                                       ElementName=volume_name, InPool=pool_instance_name,
                                                       ElementType=self.smis_base.get_ecom_int(THINPROVISIONING, '16'),
                                                       Size=self.smis_base.get_ecom_int(volume_size, '64'))
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "Error Create Volume: %(volumeName)s. Return code: %(rc)lu.  Error: %(error)s." \
                                    % {'volumeName': volume_name,
                                       'rc': rc,
                                       'error': errordesc}
                raise RuntimeError(exception_message)

        inst_name = self.smis_base.associators(job['job'], result_class='EMC_StorageVolume')

        return inst_name[0].path

    def destroy_volume(self, system_name, device_id):
        volume_instance = self.get_volume_instance(system_name, device_id)

        rc, job = self.smis_base.invoke_storage_method('ReturnElementsToStoragePool', system_name,
                                                       TheElements=[volume_instance])
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "Error Delete Volume: %(volumeName)s. Return code: %(rc)lu.  Error: %(error)s." \
                                    % {'volumeName': volume_instance['ElementName'],
                                       'rc': rc,
                                       'error': errordesc}
                raise RuntimeError(exception_message)

        return rc
