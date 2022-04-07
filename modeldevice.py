import ftntlib

class ModelDevice():
    # Class initializer
    def __init__(self, device: dict = None, fmg_api: ftntlib.fmg_jsonapi.FortiManagerJSON = None):

        self.debug = False
        self.verbose = False

        # If device dictionary was passed in on instantiation try to set the relevant values
        if device != None and not isinstance(device, dict):
            raise TypeError("CLASS ModelDevice: 'device' param when passed, must be type 'dict'")
        # Add values from device dictionary to self if they exist in dictionary, otherwise set to None
        self.adom = device['adom'] if 'adom' in device else 'root'
        self.vdom = device['vdom'] if 'vdom' in device else 'root'
        self.user = device['user'] if 'user' in device else 'admin'
        self.password = device['password'] if 'password' in device else ''
        self.descr = device['descr'] if 'descr' in device else ''
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

        # If fmg_api param was passed in, then try to set it (see also api property and setter)
        if fmg_api != None: self.api = fmg_api

    # Make api a property so that we can control the values through instantiation or direct set
    @property
    def api(self):
        return (self._api)

    @api.setter
    def api(self, myval):
        if isinstance(myval, ftntlib.fmg_jsonapi.FortiManagerJSON):
            self._api = myval
        else:
            raise TypeError("CLASS ModelDevice: fmg_api param must be an object type "
                            "fntlib.fmg.jsonapi.FortiManagerJSON")


    # Object stringification
    def __str__(self):
        # Return all instance variables as string
        return str(vars(self))


    def __api_result(self, a_response):
        if a_response[0]['message'] == 'OK':
            return True
        else:
            return False

    # Function to analyze task based FMG API call results
    def __api_task_result(self, a_taskid):
        task = self.api.taskwait(a_taskid)  # ftntlib class function
        if task[1]['num_err'] > 0:
            return False
        else:
            return True

    # Add the current model device object to FMG via passed in ftntlib 'api'
    def add(self):

        # Check parameters required for 'add'
        if self.adom is None: raise MdDataError('adom', 'add')
        if self.vdom is None: raise MdDataError('vdom', 'add')
        if self.name is None: raise MdDataError('name', 'add')
        if self.serial_num is None: raise MdDataError('serial_num', 'add')
        if self.platform is None: raise MdDataError('platform', 'add')
        if self.preferred_img is None: raise MdDataError('preferred_img', 'add')

        # If both device name and serial exist in dvm check to see if they are for the same device, if so raise except
        if self.check_dev_name_in_fmg():
            raise MdFmgDvmError(f'Device with name {self.name} already exists in FMG DVM, aborting')

        url = 'dvm/cmd/add/device'
        data = {
            'adom': self.adom,
            'flags': ['create_task',
                      'nonblocking'],
            'device': {
                "adm_pass": self.password,
                "adm_usr": self.user,
                "desc": self.descr,
                "dev_status": 1,
                "device_action": "add_model",
                'flags': 69468160,  # Without this auto-install stuff doesn't happen when match device registers
                "meta fields": self.meta_vars,
                "mgmt_mode": 3,
                "model_device": 1,
                "mr": 0,
                "name": self.name,
                "sn": self.serial_num,
                "os_type": 0,
                "os_ver": 7,
                "platform_str": self.platform,
                "prefer_img_ver": self.preferred_img  # matching text displayed in GUI for avail builds doesnt work
            }
        }
        response = self.api.execute(url, data)
        taskid = response[1]['taskid']
        return self.__api_task_result(taskid)

    # Add the current model device object to FMG via passed in ftntlib 'api'
    def delete(self):

        # Check parameters required for 'add'
        if self.adom is None: raise MdDataError('adom', 'delete')
        if self.vdom is None: raise MdDataError('vdom', 'delete')
        if self.name is None: raise MdDataError('name', 'delete')

        #If both device name and serial exist in dvm check to see if they are for the same device, if so raise except
        if self.check_dev_name_in_fmg():
            # If serial number is set, check to see if name and serial number associated in dvmdb
            # If serial number is not set do not do this check and continue
            if self.serial_num is not None:
                if self.check_exist_dev_name_and_sn_same():
                    url = 'dvm/cmd/del/device/'
                    data = {
                        'adom': self.adom,
                        'flags': ['create_task',
                                  'nonblocking'],
                        'device': self.name
                    }
                    response = self.api.execute(url, data)
                    # taskid = response[1]['taskid']
                    # return self.__api_task_result(taskid)

                    # For some reason delete will not create a task so using api OK check
                    return self.__api_result(response)
                else:
                    raise MdFmgDvmError('Supplied device name and sn are not associated in fmg dvmdb')
        else:
            pass

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
        response = self.api.add(url, data)
        return self.__api_result(response)

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
        response = self.api.execute(url, data)
        # This install requires to check task to verify completion
        taskid = response[1]['task']
        return self.__api_task_result(taskid)

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
        response = self.api.add(url, data)
        return self.__api_result(response)


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
        response = self.api.add(url, data)
        return self.__api_result(response)

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
        }
        response = self.api.add(url, data)
        return self.__api_result(response)

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
        }
        response = self.api.add(url, data)
        return self.__api_result(response)

    def get_templ_group(self):
        # Check for required parameters
        if self.adom is None: raise MdDataError('adom', 'add_to_cli_templ_group')
        if self.vdom is None: raise MdDataError('vdom', 'add_to_cli_templ_group')
        if self.name is None: raise MdDataError('name', 'add_to_cli_templ_group')
        if self.template_group is None: raise MdDataError('sdwan_template', 'add_to_cli_templ_group')

        # url = f'/pm/config/adom/{self.adom}/tmplgrp/{self.template_group}/scope member'
        url = f'/pm/tmplgrp/adom/{self.adom}/{self.template_group}/'
        data = {
        }
        response = self.api.get(url, data)
        return response
        # return self.__api_result(response)

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
        response = self.api.add(url, data)
        return self.__api_result(response)


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
        response = self.api.execute(url, data)

        # This call requires to check task to verify completion
        taskid = response[1]['task']
        return self.__api_task_result(taskid)

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
        response = self.api.get(url, data)
        return True if response[1] else False

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
        response = self.api.get(url, data)
        return True if response[1] else False

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
        response = self.api.get(url,data)
        return True if response[1][0]['sn'] == self.serial_num else False

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