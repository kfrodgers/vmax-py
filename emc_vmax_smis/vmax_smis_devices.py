# Copyright 2016 EMC Corporation

import time
from vmax_smis_base import VmaxSmisBase


class VmaxSmisDevices(object):
    def __init__(self, **kwargs):
        self.refresh = False
        self.devices = None

        self.interval = 30
        self.refresh_time = 0

        for attr in kwargs.keys():
            setattr(self, attr, kwargs[attr])

        if not hasattr(self, 'smis_base'):
            self.smis_base = VmaxSmisBase(**kwargs)

    def _reset(self):
        current_time = time.time()
        if (current_time > self.refresh_time) or ((current_time + self.interval) < self.refresh_time):
            self.refresh_time = current_time + self.interval
            self.refresh = True

    def _load_all_devices(self):
        if self.refresh or self.devices is None:
            self.devices = self.smis_base.list_storage_volumes()
            self.refresh = False

        return self.devices

    def get_volume_instance(self, system_name, device_id):
        for volume in self._load_all_devices():
            if volume['SystemName'] == system_name and volume['DeviceID'] == device_id:
                break
        else:
            raise ReferenceError('%s - %s: volume not found' % (system_name, device_id))

        return volume

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

    def get_extended_volume(self, system_name, device_id):
        return self.smis_base.get_instance(self.get_volume_instance(system_name, device_id))

    def get_volume_size(self, system_name, device_id):
        extended_volume = self.get_extended_volume(system_name, device_id)

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

    def get_volume_properties(self, system_name, device_id, requested_props):
        extended_volume = self.get_extended_volume(system_name, device_id)

        properties = {}

        properties_list = extended_volume.properties.items()
        for p in properties_list:
            for req in requested_props:
                if req == p[0]:
                    cim_properties = p[1]
                    properties[p[0]] = unicode(cim_properties.value)
                    break
            else:
                properties[p[0]] = None

        return properties

    def get_storage_group(self, system_name, device_id):
        instances = self.smis_base.list_storage_groups_from_volume(self.get_volume_instance(system_name, device_id))
        groups = []
        for i in instances:
            groups.append(i['InstanceID'])
        return groups
