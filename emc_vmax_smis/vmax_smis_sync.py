# Copyright 2016 EMC Corporation

import time
from vmax_smis_base import VmaxSmisBase

THINPROVISIONINGCOMPOSITE = 32768
THINPROVISIONING = 5


class VmaxSmisSync(object):
    def __init__(self, **kwargs):
        self.sync_sv_refresh = False
        self.sync_svs = None

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
            self.sync_sv_refresh = True

    def _load_all_sync_sv(self):
        if self.sync_sv_refresh or self.sync_svs is None:
            self.sync_svs = self.smis_base.list_se_storage_synchronized_sv_sv()
            self.sync_sv_refresh = False

        return self.sync_svs

    @staticmethod
    def get_sync_source(sync_sv):
        return sync_sv['SystemElement']

    @staticmethod
    def get_sync_target(sync_sv):
        return sync_sv['SyncedElement']

    def get_sync_sv_source_devices(self, system_name):
        sources = []
        for sync_sv in self._load_all_sync_sv():
            source = self.get_sync_source(sync_sv)
            if source['SystemName'] == system_name:
                sources.append(source['DeviceId'])

        return sorted(set(sources))

    def get_sync_sv_target_devices(self, system_name):
        targets = []
        for sync_sv in self._load_all_sync_sv():
            target = self.get_sync_target(sync_sv)
            if target['SystemName'] == system_name:
                targets.append(target['DeviceId'])

        return sorted(set(targets))

    def get_sync_sv_devices(self, system_name):
        devices = []
        devices.extend(self.get_sync_sv_source_devices(system_name))
        devices.extend(self.get_sync_sv_target_devices(system_name))
        return sorted(set(devices))

    def get_sync_sv_by_device(self, system_name, device_id):
        for sync_sv in self._load_all_sync_sv():
            source = self.get_sync_source(sync_sv)
            target = self.get_sync_target(sync_sv)
            if source['SystemName'] == system_name and device_id in [source['DeviceID'], target['DeviceId']]:
                break
        else:
            raise ReferenceError('%s - %s: sync sv not found' % (system_name, device_id))

        return sync_sv

    def get_sync_sv_by_source(self, system_name, device_id):
        for sync_sv in self._load_all_sync_sv():
            source = self.get_sync_source(sync_sv)
            if source['SystemName'] == system_name and source['DeviceID'] == device_id:
                break
        else:
            raise ReferenceError('%s - %s: sync sv not found' % (system_name, device_id))

        return sync_sv

    def get_sync_sv_by_target(self, system_name, device_id):
        for sync_sv in self._load_all_sync_sv():
            target = self.get_sync_target(sync_sv)
            if target['SystemName'] == system_name and target['DeviceID'] == device_id:
                break
        else:
            raise ReferenceError('%s - %s: sync sv not found' % (system_name, device_id))

        return sync_sv

    def delete_sync_relationship(self, system_name, sync_sv, force=False):
        rep_service = self.smis_base.find_replication_service(system_name)
        rc, job = self.smis_base.invoke_method('ModifyReplicaSynchronization', rep_service,
                                               Operation=self.smis_base.get_ecom_int(8, '16'),
                                               Synchronization=sync_sv, Force=force)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "Error break clone relationship: Sync Name: %(syncName)s " \
                                   "Return code: %(rc)lu.  Error: %(error)s." \
                                   % {'syncName': sync_sv, 'rc': rc, 'error': errordesc}
                raise RuntimeError(exception_message)

        return rc
