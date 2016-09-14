# Copyright 2016 EMC Corporation

import time
from vmax_smis_base import VmaxSmisBase

SMIS_TYPE_Mirror = 6
SMIS_TYPE_Snapshot = 7
SMIS_TYPE_Clone = 8
SMIS_TYPE_TokenizedClone = 9

SMIS_OP_Abort = 2
SMIS_OP_ActivateConsistency = 3
SMIS_OP_Activate = 4
SMIS_OP_AddSyncPair = 5
SMIS_OP_DeactivateConsistency = 6
SMIS_OP_Deactivate = 7
SMIS_OP_Detach = 8
SMIS_OP_Dissolve = 9
SMIS_OP_Failover = 10
SMIS_OP_Failback = 11
SMIS_OP_Fracture = 12
SMIS_OP_RemoveSyncPair = 13
SMIS_OP_ResyncReplica = 14
SMIS_OP_RestorefromReplica = 15
SMIS_OP_Resume = 16
SMIS_OP_ResetToSync = 17
SMIS_OP_ResetToAsync = 18
SMIS_OP_ReturnToResourcePool = 19
SMIS_OP_ReverseRoles = 20
SMIS_OP_Split = 21
SMIS_OP_Suspend = 22
SMIS_OP_Unprepare = 23
SMIS_OP_Prepare = 24
SMIS_OP_ResettoAdaptive = 25


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
        sync_svs = []
        for sync_sv in self._load_all_sync_sv():
            source = self.get_sync_source(sync_sv)
            target = self.get_sync_target(sync_sv)
            if source['SystemName'] == system_name and device_id in [source['DeviceID'], target['DeviceId']]:
                sync_svs.append(sync_sv)

        if len(sync_svs) == 0:
            raise ReferenceError('%s - %s: sync sv not found' % (system_name, device_id))

        return sync_svs

    def get_sync_sv_by_source(self, system_name, device_id):
        sync_svs = []
        for sync_sv in self._load_all_sync_sv():
            source = self.get_sync_source(sync_sv)
            if source['SystemName'] == system_name and source['DeviceID'] == device_id:
                sync_svs.append(sync_sv)

        if len(sync_svs) == 0:
            raise ReferenceError('%s - %s: sync sv not found' % (system_name, device_id))

        return sync_svs

    def get_sync_sv_by_target(self, system_name, device_id):
        for sync_sv in self._load_all_sync_sv():
            target = self.get_sync_target(sync_sv)
            if target['SystemName'] == system_name and target['DeviceID'] == device_id:
                break
        else:
            raise ReferenceError('%s - %s: sync sv not found' % (system_name, device_id))

        return sync_sv

    def get_sync_sv_properties(self, sync_sv_name, property_list=None):
        sync_sv_instance = self.smis_base.get_instance(sync_sv_name, property_list=property_list)

        properties = {}
        for p in sync_sv_instance.items():
            properties[p[0]] = p[1]

        return properties

    def deactivate_sync_relationship(self, system_name, sync_sv, force=False):
        return self.modify_sync_relationship(system_name, sync_sv, SMIS_OP_Deactivate, force=force)

    def detach_sync_relationship(self, system_name, sync_sv, force=False):
        return self.modify_sync_relationship(system_name, sync_sv, SMIS_OP_Detach, force=force)

    def dissolve_sync_relationship(self, system_name, sync_sv, force=False):
        return self.modify_sync_relationship(system_name, sync_sv, SMIS_OP_Dissolve, force=force)

    def modify_sync_relationship(self, system_name, sync_sv, operation, force=False):
        rep_service = self.smis_base.find_replication_service(system_name)
        rc, job = self.smis_base.invoke_method('ModifyReplicaSynchronization', rep_service,
                                               Operation=self.smis_base.get_ecom_int(operation, '16'),
                                               Synchronization=sync_sv, Force=force)
        if rc != 0:
            rc, errordesc = self.smis_base.wait_for_job_complete(job['job'])
            if rc != 0:
                exception_message = "Error modify sync relationship %(op)lu: Sync Name: %(syncName)s " \
                                    "Return code: %(rc)lu.  Error: %(error)s." \
                                    % {'op': operation, 'syncName': sync_sv, 'rc': rc, 'error': errordesc}
                raise RuntimeError(exception_message)

        return rc
