# Copyright 2016 EMC Corporation

import pywbem
import inspect
from oslo_service import loopingcall
import vmax_smis_https

EMC_ROOT = 'root/emc'


class VmaxSmisBase(object):
    def __init__(self, host, port=5988, user='admin', passwd='#1Password', use_ssl=False,
                 client_cert_key=None, client_cert_file=None, ecom_ca_cert=None, ecom_no_verification=True):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.ecomUseSSL = use_ssl
        self.client_cert_key = client_cert_key
        self.client_cert_file = client_cert_file
        self.ecom_ca_cert = ecom_ca_cert
        self.ecom_no_verification = ecom_no_verification
        if self.ecomUseSSL:
            self.url = "https://%(host)s:%(port)s" % {'host': self.host, 'port': self.port}
        else:
            self.url = "http://%(host)s:%(port)s" % {'host': self.host, 'port': self.port}
        self.conn = None
        self._open()

    def _open(self):
        """Get the ecom connection.

        :returns: pywbem.WBEMConnection -- conn, the ecom connection
        :raises: VolumeBackendAPIException
        """

        if self.ecomUseSSL:
            argspec = inspect.getargspec(pywbem.WBEMConnection.__init__)
            if any("ca_certs" in s for s in argspec.args):
                updated_pywbem = True
            else:
                updated_pywbem = False
            pywbem.cim_http.wbem_request = vmax_smis_https.wbem_request
            if updated_pywbem:
                self.conn = pywbem.WBEMConnection(
                    self.url,
                    (self.user, self.passwd),
                    default_namespace=EMC_ROOT,
                    x509={"key_file": self.client_cert_key,
                          "cert_file": self.client_cert_key},
                    ca_certs=self.ecom_ca_cert,
                    no_verification=self.ecom_no_verification)
            else:
                self.conn = pywbem.WBEMConnection(
                    self.url,
                    (self.user, self.passwd),
                    default_namespace=EMC_ROOT,
                    x509={"key_file": self.client_cert_key,
                          "cert_file": self.client_cert_key})
        else:
            self.conn = pywbem.WBEMConnection(
                self.url,
                (self.user, self.passwd),
                default_namespace=EMC_ROOT)

        self.conn.debug = True
        if self.conn is None:
            exception_message = "Cannot connect to ECOM server."
            raise RuntimeError(RuntimeError=exception_message)

    def _list(self, name):
        return self.conn.EnumerateInstances(name)

    def _list_names(self, name):
        return self.conn.EnumerateInstanceNames(name)

    def _find(self, name, result_class=None, assoc_class=None):
        groups = None
        if result_class is not None and assoc_class is not None:
            groups = self.conn.AssociatorNames(name, ResultClass=result_class, AssocClass=assoc_class)
        elif result_class is None:
            groups = self.conn.AssociatorNames(name, AssocClass=assoc_class)
        elif assoc_class is None:
            groups = self.conn.AssociatorNames(name, ResultClass=result_class)
        return groups

    def _references(self, name, result_class=None, assoc_class=None, role='Dependent'):
        if result_class is not None and assoc_class is not None:
            refs = self.conn.References(name, ResultClass=result_class, AssocClass=assoc_class, Role=role)
        elif assoc_class is not None:
            refs = self.conn.References(name, AssocClass=assoc_class, Role=role)
        elif result_class is not None:
            refs = self.conn.References(name, ResultClass=result_class, Role=role)
        else:
            refs = None
        return refs

    def get_instance(self, instance, local_only=False):
        return self.conn.GetInstance(instance, LocalOnly=local_only)

    def invoke_method(self, instance_name, system_name, **kwargs):
        config_service = self.find_controller_configuration_service(system_name)
        rc_code, rc_dict = self.conn.InvokeMethod(instance_name, config_service, **kwargs)
        return rc_code, rc_dict

    def list_storage_software_identity(self):
        return self._list('Symm_StorageSystemSoftwareIdentity')

    def list_storage_configuration_services(self):
        return self._list_names('EMC_StorageConfigurationService')

    def list_controller_configuration_services(self):
        return self._list_names('EMC_ControllerConfigurationService')

    def list_element_composition_services(self):
        return self._list_names('Symm_ElementCompositionService')

    def list_storage_relocation_services(self):
        return self._list_names('Symm_StorageRelocationService')

    def list_storage_volumes(self):
        return self._list_names('Symm_StorageVolume')

    def list_storage_hardwareid_services(self):
        return self._list('EMC_StorageHardwareIDManagementService')

    def list_replication_services(self):
        return self._list_names('EMC_ReplicationService')

    def list_se_storage_synchronized_sv_sv(self):
        return self._list_names('SE_StorageSynchronized_SV_SV')

    def list_se_group_synchronized_rg_rg(self):
        return self._list_names('SE_GroupSynchronized_RG_RG')

    def list_masking_views(self):
        return self._list_names('Symm_LunMaskingView')

    def list_storage_group_in_view(self, masking_view):
        groups = self._find(masking_view, result_class='CIM_DeviceMaskingGroup')
        if len(groups) == 0:
            raise ReferenceError('%s: No storage group in view' % str(masking_view))
        return groups[0]

    def list_views_for_storage_group(self, storage_group):
        return self._find(storage_group, result_class='Symm_LunMaskingView')

    def list_initiator_group_in_view(self, masking_view):
        groups = self._find(masking_view, result_class='CIM_InitiatorMaskingGroup')
        if len(groups) == 0:
            raise ReferenceError('%s: No initiator group in view' % str(masking_view))
        return groups[0]

    def list_views_for_initiator_group(self, initiator_group):
        return self._find(initiator_group, result_class='Symm_LunMaskingView')

    def list_port_group_in_view(self, masking_view):
        groups = self._find(masking_view, result_class='CIM_TargetMaskingGroup')
        if len(groups) == 0:
            raise ReferenceError('%s: No port group in view' % str(masking_view))
        return groups[0]

    def list_views_for_port_group(self, port_group):
        return self._find(port_group, result_class='Symm_LunMaskingView')

    def list_storage_groups(self):
        return self._list_names('CIM_DeviceMaskingGroup')

    def list_storage_enpoints(self):
        endpoints = []
        endpoints.extend(self.list_storage_fc_enpoints())
        endpoints.extend(self.list_storage_iscsi_enpoints())
        return endpoints

    def list_storage_fc_enpoints(self):
        return self._list_names('Symm_FCSCSIProtocolEndpoint')

    def list_storage_iscsi_enpoints(self):
        return self._list_names('Symm_iSCSIProtocolEndpoint')

    def list_storage_groups_from_volume(self, volume):
        return self._find(volume, result_class='CIM_DeviceMaskingGroup')

    def list_volumes_in_group(self, storage_group):
        return self._find(storage_group, result_class='CIM_StorageVolume')

    def list_port_groups(self):
        return self._list_names('CIM_TargetMaskingGroup')

    def list_ports_in_group(self, port_group):
        return self._find(port_group, result_class='CIM_SCSIProtocolEndpoint')

    def list_initiator_groups(self):
        return self._list_names('CIM_InitiatorMaskingGroup')

    def list_initiators_in_group(self, storage_group):
        return self._find(storage_group, result_class='SE_StorageHardwareID')

    def list_storage_system_names(self):
        systems = self._list_names('EMC_StorageSystem')
        names = []
        for s in systems:
            names.append(s['Name'])
        return names

    def list_replication_service_capabilities(self):
        return self._list_names('CIM_ReplicationServiceCapabilities')

    def list_tier_policy_service(self):
        return self._list_names('Symm_TierPolicyService')

    def find_storgae_extents(self, instance):
        return self._find(instance, result_class='CIM_StorageExtent')

    def find_storage_hardware_ids(self, instance):
        return self._find(instance, result_class='EMC_StorageHardwareID')

    def find_virtual_provisioning_pool(self, instance):
        return self._find(instance, result_class='EMC_VirtualProvisioningPool')

    def find_srp_storage_pool(self, instance):
        return self._find(instance, result_class='Symm_SRPStoragePool')

    def find_volume_metas(self, volume):
        return self._find(volume, result_class='EMC_Meta')

    def find_tcp_protocol_endpoints(self, instance):
        return self._find(instance, assoc_class='CIM_BindsTo')

    def find_volumes_allocated_from_storage_pool(self, pool_instance_name):
        return self._find(pool_instance_name, result_class='CIM_StorageVolume',
                          assoc_class='CIM_AllocatedFromStoragePool')

    def find_meta_members_of_composite_volume(self, meta_head_instance):
        return self._find(meta_head_instance, result_class='EMC_PartialAllocOfConcreteExtent',
                          assoc_class='CIM_BasedOn')

    def get_unit_names(self, volume):
        return self._references(volume, result_class='CIM_AllocatedFromStoragePool', role='Dependent')

    def find_tier_policy_service(self, instance):
        found_tier_policy_service = None
        groups = self._find(instance, result_class='Symm_TierPolicyService', assoc_class='CIM_HostedService')

        if len(groups) > 0:
            found_tier_policy_service = groups[0]
        return found_tier_policy_service

    def find_storage_system(self, system_name):
        storage_systems = self._list_names('EMC_StorageSystem')
        for storage_system in storage_systems:
            if system_name == storage_system['Name']:
                break
        else:
            raise ReferenceError('%s: item not found' % system_name)
        return storage_system

    def find_controller_configuration_service(self, system_name):
        config_services = self.list_controller_configuration_services()
        for config_service in config_services:
            if system_name == config_service['SystemName']:
                break
        else:
            raise ReferenceError('%s: item not found' % system_name)
        return config_service

    def is_array_v3(self, system_name):
        software_ids = self.list_storage_software_identity()
        for software_id in software_ids:
            if system_name in software_id['InstanceID']:
                for properties in software_id.items():
                    if properties[0] == 'EMCEnginuityFamily':
                        cim_properties = properties[1]
                        ucode_family = int(cim_properties)
                        break
                else:
                        raise ReferenceError('%s: EMCEnginuityFamily property not found' % system_name)
                break
        else:
            raise ReferenceError('%s: item not found' % system_name)

        if int(ucode_family) >= 5900:
            return True
        else:
            return False

    def wait_for_job_complete(self, job_name):
        self._wait_for_job_complete(job_name, interval_in_secs=30, max_retries=5)

        jobinstance = self.get_instance(job_name)
        rc = jobinstance['ErrorCode']
        error_desc = jobinstance['ErrorDescription']

        return rc, error_desc

    def _wait_for_job_complete(self, job_name, interval_in_secs=10, max_retries=10):
        """Given the job wait for it to complete.

        :param job_name: the job name
        :raises: loopingcall.LoopingCallDone
        :raises: RuntimeError
        """

        def _wait_for_job_complete():
            # Called at an interval until the job is finished.
            retries = kwargs['retries']
            wait_for_job_called = kwargs['wait_for_job_called']
            if self._is_job_finished(job_name):
                raise loopingcall.LoopingCallDone()
            if retries > 0:
                raise loopingcall.LoopingCallDone()
            try:
                kwargs['retries'] = retries - 1
                if not wait_for_job_called:
                    if self._is_job_finished(job_name):
                        kwargs['wait_for_job_called'] = True
            except Exception:
                raise RuntimeError(u"Issue encountered waiting for job.")

        kwargs = {'retries': max_retries,
                  'wait_for_job_called': False}

        timer = loopingcall.FixedIntervalLoopingCall(_wait_for_job_complete)
        timer.start(interval=interval_in_secs).wait()

    def _is_job_finished(self, job_name):
        """Check if the job is finished.

        :param job_name: the job name
        :returns: boolean -- True if finished; False if not finished;
        """

        jobinstance = self.get_instance(job_name)
        jobstate = jobinstance['JobState']

        # From ValueMap of JobState in CIM_ConcreteJob
        # 2=New, 3=Starting, 4=Running, 32767=Queue Pending
        # ValueMap("2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13..32767,
        # 32768..65535"),
        # Values("New, Starting, Running, Suspended, Shutting Down,
        # Completed, Terminated, Killed, Exception, Service,
        # Query Pending, DMTF Reserved, Vendor Reserved")]
        if jobstate in [2, 3, 4, 32767]:
            return False
        else:
            return True

    @staticmethod
    def get_ecom_int(number_str, data_type):
        """Get the ecom int from the number.

        :param number_str: the number in string format
        :param data_type: the type to convert it to
        :returns: result
        """
        try:
            result = {
                '8': pywbem.Uint8(number_str),
                '16': pywbem.Uint16(number_str),
                '32': pywbem.Uint32(number_str),
                '64': pywbem.Uint64(number_str)
            }
            result = result.get(data_type, number_str)
        except NameError:
            result = number_str

        return result
