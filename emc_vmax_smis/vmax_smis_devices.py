# Copyright 2016 EMC Corporation

import time
from vmax_smis_base import VmaxSmisBase

THINPROVISIONINGCOMPOSITE = 32768
THINPROVISIONING = 5


class VmaxSmisDevices(object):
    def __init__(self, **kwargs):
        self.devices_refresh = False
        self.devices = None

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
            self.devices_refresh = True

    def _load_all_devices(self):
        if self.devices_refresh or self.devices is None:
            self.devices = self.smis_base.list_storage_volumes(property_list=['ElementName', 'SystemName',
                                                                              'DeviceID', 'SpaceConsumed',
                                                                              'ConsumableBlocks', 'BlockSize',
                                                                              'EMCIsMapped', 'IsComposite', 'Usage'])
            self.devices_refresh = False

        return self.devices

    def get_volume_instance(self, system_name, device_id):
        for volume in self._load_all_devices():
            if volume['SystemName'] == system_name and volume['DeviceID'] == device_id:
                break
        else:
            raise ReferenceError('%s - %s: volume not found' % (system_name, device_id))

        return volume

    def get_volume_instance_name(self, system_name, device_id):
        volume_instance = self.get_volume_instance(system_name, device_id)
        return volume_instance.path

    def get_volume_instance_names(self, system_name, device_ids):
        volumes = []
        for dev in device_ids:
            volumes.append(self.get_volume_instance_name(system_name, dev))
        return volumes

    def get_volume_by_name(self, system_name, volume_name):
        for volume in self._load_all_devices():
            if volume['SystemName'] == system_name and volume['ElementName'] == volume_name:
                break
        else:
            raise ReferenceError('%s - %s: volume not found' % (system_name, volume_name))

        return volume['DeviceID']

    def list_all_devices(self, system_name):
        devices = []
        for volume in self._load_all_devices():
            if volume['SystemName'] == system_name:
                devices.append(volume['DeviceID'])
        return devices

    def list_all_devices_by_name(self, system_name):
        device_names = []
        for volume in self._load_all_devices():
            if volume['SystemName'] == system_name:
                device_names.append(volume['ElementName'])
        return device_names

    def get_space_consumed(self, system_name, device_id):
        volume = self.get_volume_instance(system_name, device_id)
        return volume['SpaceConsumed']

    def get_volume_name(self, system_name, device_id):
        volume = self.get_volume_instance(system_name, device_id)
        return volume['ElementName']

    def rename_volume(self, volume_instance, new_name):
        volume_instance['ElementName'] = unicode(new_name)
        self.smis_base.modify_instance(volume_instance, property_list=['ElementName'])

    def get_extended_volume(self, system_name, device_id, property_list=None):
        volume = self.get_volume_instance(system_name, device_id)
        return self.smis_base.get_instance(volume.path, property_list=property_list)

    def get_volume_size(self, system_name, device_id):
        volume = self.get_volume_instance(system_name, device_id)

        block_size = volume['ConsumableBlocks']
        num_blocks = volume['BlockSize']

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

        return name.path

    def list_storage_pools(self, system_name):
        pool_instance_names = self._list_pool_instance_names(system_name)
        pool_instance_ids = []
        for name in pool_instance_names:
            pool_instance_ids.append(name['InstanceID'])

        return pool_instance_ids

    def get_storage_group(self, system_name, device_id):
        volume = self.get_volume_instance(system_name, device_id)
        instances = self.smis_base.list_storage_groups_from_volume(volume.path)
        groups = []
        for i in instances:
            groups.append(i['InstanceID'])
        return groups

    def get_pool_name(self, system_name, device_id):
        volume = self.get_volume_instance(system_name, device_id)
        if self.smis_base.is_array_v3(system_name):
            storage_pools = self.smis_base.find_srp_storage_pool(volume.path)
        else:
            storage_pools = self.smis_base.find_virtual_provisioning_pool(volume.path)
        pool = None
        if storage_pools is not None and len(storage_pools) == 1:
            pool = storage_pools[0]['PoolID']
        return pool

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
        self.devices_refresh = True

        return inst_name[0]['DeviceID']

    def destroy_volumes(self, system_name, device_ids):
        elements = []
        for device_id in device_ids:
            volume_instance = self.get_volume_instance(system_name, device_id)
            elements.append(volume_instance.path)

        rc, job = self.smis_base.invoke_storage_method('ReturnElementsToStoragePool', system_name,
                                                       TheElements=elements)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "Error Delete Volume: %(volumeName)s. Return code: %(rc)lu.  Error: %(error)s." \
                                    % {'volumeName': str(device_ids),
                                       'rc': rc,
                                       'error': errordesc}
                raise RuntimeError(exception_message)

        return rc
