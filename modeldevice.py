class ModelDevice:
    # Class initializer
    def __init__(self, device: dict = None, fmg_api=None, fmg_ver: int = 70):

        self.debug = False
        self.verbose = False

        # If device dictionary was passed in on instantiation try to set the relevant values
        if device is not None and not isinstance(device, dict):
            raise TypeError("CLASS ModelDevice: 'device' param when passed, must be type 'dict'")
        # Add values from device dictionary to self if they exist in dictionary, otherwise set to None
        self.adom = device['adom'] if 'adom' in device else 'root'
        self.vdom = device['vdom'] if 'vdom' in device else 'root'
        self.user = device['login'] if 'login' in device else 'admin'
        self.password = device['password'] if 'password' in device else ''
        self.descr = device['descr'] if 'descr' in device else ''
        self.device_blueprint = device['device_blueprint'] if 'device_blueprint' in device else None
        self.fmg_ver = fmg_ver
        self.name = device['name'] if 'name' in device else None
        self.serial_num = device['serial_num'] if 'serial_num' in device else None
        self.meta_vars = device['meta_vars'] if 'meta_vars' in device else ''
        self.platform = device['platform'] if 'platform' in device else None
        self.policy_package = device['policy_package'] if 'policy_package' in device else None
        self.preferred_img = device['preferred_img'] if 'preferred_img' in device else None
        self.group = device['group'] if 'group' in device else None
        self.sdwan_template = device['sdwan_template'] if 'sdwan_template' in device else None
        self.pre_cli_template = device['pre_cli_template'] if 'pre_cli_template' in device else None
        self.cli_template_group = device['cli_template_group'] if 'cli_template_group' in device else None
        self.template_group = device['template_group'] if 'template_group' in device else None
        self.psk = device['psk'] if 'psk' in device else None
        self.fmg_script = device['fmg_script'] if 'fmg_script' in device else None
        self.os_major = device['major_version'] if 'major_version' in device else 7
        self.os_minor = device['minor_version'] if 'minor_version' in device else 4
        self.os_patch = device['patch_version'] if 'patch_version' in device else 4

        if 'vdomenabled' in device:
            if device['vdomenabled'] == 'true' or device['vdomenabled'] == 'True':
                self.vdomenabled = True
        else:
            self.vdomenabled = False

        # If fmg_api param was passed in, then try to set it (see also api property and setter)
        if fmg_api is not None: self.api = fmg_api

    # Make api a property so that we can control the values through instantiation or direct set
    @property
    def api(self):
        return self._api

    @api.setter
    def api(self, myapi):
        self._api = myapi

    # Object stringification
    def __str__(self):
        # Return all instance variables as string
        return str(vars(self))

    # Function to determine result of pyfgt api requests
    def __api_result(self, code, msg):
        if code == 0:
            if 'taskid' in msg:
                # Monitor task status then return result
                return self.__api_task_result(msg.get('taskid'))
            elif 'task' in msg:
                # Monitor task status then return result
                return self.__api_task_result(msg.get('task'))
            else:
                # No error and no task, success
                return 0, None
        else:
            return 1, msg

    # Function to analyze task based FMG API call results
    def __api_task_result(self, a_taskid):
        code, msg = self.api.track_task(a_taskid)  # pyfgt class function (track_task)
        if msg['num_err'] > 0:
            return 1, msg['line'][-1]
        elif msg['num_warn'] > 0:
            return 1, msg['line'][-1]
        else:
            return 0, None

    # Add the current model device object to FMG via passed in ftntlib 'api'
    def add(self):
        # Check parameters required for 'add'
        if self.adom is None: raise MdDataError('adom', 'add')
        if self.vdom is None: raise MdDataError('vdom', 'add')
        if self.name is None: raise MdDataError('name', 'add')
        if self.serial_num is None: raise MdDataError('serial_num', 'add')
        if self.platform is None: raise MdDataError('platform', 'add')
        # if self.preferred_img is None: raise MdDataError('preferred_img', 'add')
        if self.preferred_img is None:
            self.preferred_img = ''

        # If device name already exists in FMG then raise an exception
        if self.check_dev_name_in_fmg():
            raise MdFmgDvmError(f'Device with name {self.name} already exists in FMG DVM')

        # If serial number already exists in FMG then raise an exception
        if self.check_dev_sn_in_fmg():
            raise MdFmgDvmError(f'Device with serial number {self.serial_num} already exists in FMG DVM')

        url = 'dvm/cmd/add/device'
        data = {
            'adom': self.adom,
            'flags': ['create_task'],
            'device': {
                "adm_pass": self.password,
                "adm_usr": self.user,
                "desc": self.descr,
                "dev_status": 1,
                "device_action": "add_model",  #could instead use "model_device" with value of 1
                #"flags": 67371008,  # flags copied from when device was added from csv for device blueprint
                # "flags": 69468192,  # flags copied from when device was added from csv for device blueprint 7.2.4
                "flags": 67371040,  # flags copied from when device was added from csv for device blueprint 7.4.4
                "hostname": self.name,
                "mgmt_mode": 'fmg',  # optional use "3" to represent fmg mgmt mode
                "name": self.name,
                "psk": self.psk,
                "sn": self.serial_num,
                "os_type": 'fos',  # optional use "0" to represent fos
                "os_ver": self.os_major,
                "mr": self.os_minor,
                "mr": self.os_minor,
                "patch": self.os_patch,
                "platform_str": self.platform,
                "prefer_img_ver": self.preferred_img  # matching text displayed in GUI for avail builds doesn't work
            }
        }
        if self.fmg_ver < 720:
            data['device']['meta_vars'] = self.meta_vars
            if self.device_blueprint:
                data['device']['device blueprint'] = self.device_blueprint

        rcode, rmsg = self.api.execute(url, data=data)
        return self.__api_result(rcode, rmsg)

    # Delete existing model device object from FMG via passed in ftntlib 'api'
    def delete(self):
        # Check parameters required for 'delete'
        if self.adom is None: raise MdDataError('adom', 'delete')
        # if self.vdom is None: raise MdDataError('vdom', 'delete')
        if self.name is None: raise MdDataError('name', 'delete')

        if self.check_dev_name_in_fmg():
            # If serial number is set, check to see if name and serial number associated in dvmdb
            # If serial number is not set do not do this check and continue
            if self.serial_num is not None:
                # If both device name and serial exist in dvm check to see if they are for the same device,
                # if not, raise an exception
                if self.check_exist_dev_name_and_sn_same():
                    url = 'dvm/cmd/del/device/'
                    data = {
                        'adom': self.adom,
                        'flags': ['create_task',
                                  'nonblocking'],
                        'device': self.name
                    }

                    rcode, rmsg = self.api.execute(url, data=data)
                    return self.__api_result(rcode, rmsg)

                else:
                    raise MdFmgDvmError('Supplied device name and sn are not associated in fmg dvmdb')
        else:
            return 0, f'Device with device name {self.name} does not exist'

    # Function to assign model device to pre-run CLI template
    def add_to_pre_cli_script(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_pre_cli_script')
        if self.name is None: raise MdDataError('name', 'add_to_pre_cli_script')
        if self.pre_cli_template is None: raise MdDataError('pre_cli_template', 'add_to_pre_cli_script')

        url = f'/pm/config/adom/{self.adom}/obj/cli/template/{self.pre_cli_template}/scope member'
        data = {
            "name": self.name,
            "vdom": 'global'  # Must set this to global, not sure why...
        }
        response = self.api.add(url, data=data)
        return self.__api_result(response[1]['status']['code'],response[1]['status']['message'])

    # Function to quick install settings for device to device DB (for pre-run cli template assign)
    def install_device_db(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'install_device_db')
        if self.vdom is None: raise MdDataError('vdom', 'install_device_db')
        if self.name is None: raise MdDataError('name', 'install_device_db')

        url = f'/securityconsole/install/device'
        data = {
            "adom": self.adom,
            "scope": {
                "name": self.name,
                "vdom": self.vdom
            }
        }
        rcode, rmsg = self.api.execute(url, data=data)
        return self.__api_result(rcode, rmsg)

    # Function to add device to device group
    def add_to_dev_group(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_dev_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_dev_group')
        if self.name is None: raise MdDataError('name', 'add_to_dev_group')
        if self.group is None: raise MdDataError('group', 'add_to_dev_group')

        url = f'/dvmdb/adom/{self.adom}/group/{self.group}/object member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        rcode, rmsg = self.api.add(url, data=data)
        return self.__api_result(rcode, rmsg)

    # Function to add device to device group
    def get_dev_group_info(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_dev_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_dev_group')
        if self.name is None: raise MdDataError('name', 'add_to_dev_group')
        if self.group is None: raise MdDataError('group', 'add_to_dev_group')

        url = f'/dvmdb/adom/{self.adom}/group/{self.group}/object member'
        data = {
        }
        rcode, rmsg = self.api.get(url, data=data)
        return rmsg

    # Function to add device to sdwan template
    def add_to_sdwan_templ(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_sdwan_template')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_sdwan_template')
        if self.name is None: raise MdDataError('name', 'add_to_sdwan_template')
        if self.sdwan_template is None: raise MdDataError('sdwan_template', 'add_to_sdwan_template')

        url = f'/pm/wanprof/adom/{self.adom}/{self.sdwan_template}/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        rcode, rmsg = self.api.add(url, data=data)
        return self.__api_result(rcode, rmsg)

    # Function to add device to CLI template group
    def add_to_cli_templ_group(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.cli_template_group is None: raise MdDataError('sdwan_template', 'add_to_cli_templ_group')

        url = f'/pm/config/adom/{self.adom}/obj/cli/template-group/{self.cli_template_group}/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
            # "vdom": "global"
        }
        rcode, rmsg = self.api.add(url, data=data)
        return self.__api_result(rcode, rmsg)

    # Function to add device to fmg template group (regular "gui" template group not cli template group)
    def add_to_templ_group(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.template_group is None: raise MdDataError('sdwan_template', 'add_to_cli_templ_group')

        # url = f'/pm/config/adom/{self.adom}/tmplgrp/{self.template_group}/scope member'
        url = f'/pm/tmplgrp/adom/{self.adom}/{self.template_group}/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
            # "vdom": "global"
        }

        rcode, rmsg = self.api.add(url, data=data)
        return self.__api_result(rcode, rmsg)

    # FMG 7.2 new fmg meta vars, add mapping to existing meta var
    def add_fmg_meta_vars_mapping(self):
        if self.meta_vars == None:
            return 0, None

        meta_failed_list = []
        for i in self.meta_vars:
            print(f'  << Adding: {i} >>')

            url = f'/pm/config/adom/{self.adom}/obj/fmg/variable/{i}/dynamic_mapping'
            data = {
                "_scope": {
                    "name": f"{self.name}",
                    "vdom": f"global"
                    # "vdom": f"{self.vdom}"
                },
                "value": f"{self.meta_vars[i]}"
            }

            rcode, rmsg = self.api.add(url, data=data)
            if rcode == 0:
                print(f'     Success adding {i}')
            else:
                print(f'    Failed to add {i}')
                meta_failed_list.append(i)

        
        print('----------------------------------------------------------------------------------------------------')
        print('<--Overall Result of Meta Var Adds-->')

        if len(meta_failed_list) > 0:
            print(f'List of meta vars that failed: {meta_failed_list}')
            print('----------------------------------------------------------------------------------------------------')
            return self.__api_result(1, 'failed')
        else:
            print('All Metvars added Successfully')
            print('----------------------------------------------------------------------------------------------------')
            return(0, 'Success')

    def get_templ_group(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.template_group is None: raise MdDataError('sdwan_template', 'add_to_cli_templ_group')

        # url = f'/pm/config/adom/{self.adom}/tmplgrp/{self.template_group}/scope member'
        url = f'/pm/tmplgrp/adom/{self.adom}/{self.template_group}'
        data = {
        }
        rcode, rmsg = self.api.execute(url, data)
        return self.__api_result(rcode, rmsg)

    # Function to add device to policy package
    def add_to_pol_pkg(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_pol_pkg')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_pol_pkg')
        if self.name is None: raise MdDataError('name', 'add_to_pol_pkg')
        if self.policy_package is None: raise MdDataError('policy_package', 'add_to_pol_pkg')

        url = f'/pm/pkg/adom/root/{self.policy_package}/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        rcode, rmsg = self.api.add(url, data)
        return self.__api_result(rcode, rmsg)

    # Function to install previously assigned policy package to policy DB
    def install_pol_pkg_to_db(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'install_pol_pkg_to_db')
        if self.vdom is None: raise MdDataError('vdom', 'ainstall_pol_pkg_to_db')
        if self.name is None: raise MdDataError('name', 'install_pol_pkg_to_db')
        if self.policy_package is None: raise MdDataError('policy_package', 'install_pol_pkg_to_db')

        url = f'/securityconsole/install/package'
        data = {
            "adom": self.adom,
            "pkg": self.policy_package,
            "scope": {
                "name": self.name,
                "vdom": self.vdom
            }
        }
        rcode, rmsg = self.api.execute(url, data)
        return self.__api_result(rcode, rmsg)

    # Check if this object's name is already used as a device name in FMG DVM
    def check_dev_name_in_fmg(self):
        # Can't run if name parameter is not set (if not set return none)
        if self.name is None: return None

        url = "dvmdb/device/"
        data = {
            'filter': [
                ['name', '==', self.name]
            ],
            'fields': ['sn']
        }
        rcode, rmsg = self.api.get(url, data)
        if rcode == 0:
            # If any values returned for this filter then a matching device was found
            if len(rmsg) > 0:
                return True
            else:
                return False
        else:
            return 0

    # Check if this object's serial number is already registered in FMG DVM
    def check_dev_sn_in_fmg(self):
        # Can't run if serial_num parameter is not set (if not set return none)
        if self.serial_num is None: return None

        url = "dvmdb/device/"
        data = {
            'filter': [
                ['sn', '==', self.serial_num]
            ],
            'fields': ['name']
        }
        rcode, rmsg = self.api.get(url, data)
        if rcode == 0:
            # If any values returned for this filter then a matching device was found
            if len(rmsg) > 0:
                return True
            else:
                return False
        else:
            return 0

    # If this object's name exists in FMG DVM, check if the serial number matches this object's serail number
    def check_exist_dev_name_and_sn_same(self):
        # Can't run without name and serial_number params, return None if one is missing
        if self.name is None: return None
        if self.serial_num is None: return None

        url = "dvmdb/device/"
        data = {
            'filter': [
                ['name', '==', self.name]
            ],
            'fields': ['sn']
        }
        rcode, rmsg = self.api.get(url, data)
        # Return true if device name in FMG is associated to SN defined for this object
        return True if rmsg[0]['sn'] == self.serial_num else False

    def get_device_info(self):
        # Can't run without name and serial_number params, return None if one is missing
        if self.name is None: return None
        if self.serial_num is None: return None

        url = "dvmdb/device/"
        data = {
            'filter': [
                ['name', '==', self.name]
            ]
        }
        rcode, rmsg = self.api.get(url, data)
        return rmsg

    # function to check exists a pre-exiting script on fmg
    def check_fmg_script(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.fmg_script is None: raise MdDataError('fmg_script', 'add_to_cli_templ_group')

        url = f'/dvmdb/script/{self.fmg_script}'

        data = {
        }
        rcode, rmsg = self.api.get(url, data)
        return self.__api_result(rcode, rmsg)

    # function to execute a pre-exiting script on fmg against device
    def execute_fmg_script(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.fmg_script is None: raise MdDataError('fmg_script', 'add_to_cli_templ_group')

        url = f'/dvmdb/script/execute'

        data = {
            "adom": "root",
            "scope": {
                "name": self.name,
                "vdom": self.vdom
            },
            "script": self.fmg_script
        }
        rcode, rmsg = self.api.get(url, data)
        return self.__api_result(rcode, rmsg)

    # function to execute a pre-exiting script on fmg against device
    def execute_fmg_script_to_device(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.fmg_script is None: raise MdDataError('fmg_script', 'add_to_cli_templ_group')

        url = f'/dvmdb/adom/{self.adom}/script/execute'

        data = {
            "name": self.fmg_script,
            "vdom": self.vdom
        }
        rcode, rmsg = self.api.execute(url, data)
        return self.__api_result(rcode, rmsg)


# Custom Exception Class for this ModelDevice Class errors related to data/parameters
class MdDataError(Exception):
    def __init__(self, message1, message2):
        if message1:
            self.message1 = message1
        if message2:
            self.message2 = message2
        else:
            self.message = None

    def __str__(self):
        if self.message1 and self.message2:
            return f'\"{self.message1}\" parameter is required for method \"{self.message2}()\"'
        elif self.message1:
            return f'\"{self.message1}\" parameter is required but not set.'
        else:
            return f'Error, value invalid or not set'


# Custom Exception Class for this ModelDevice Class errors related to FMG DVM
class MdFmgDvmError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'{self.message}'
        else:
            return f'MdFmgDvmError has been raised'
