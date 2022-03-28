import ftntlib

class ModelDevice():
    # Class initializer
    def __init__(self, device: dict = None, fmg_api: ftntlib.fmg_jsonapi.FortiManagerJSON = None):

        if fmg_api != None:
            if isinstance(fmg_api, ftntlib.fmg_jsonapi.FortiManagerJSON):
                self.api = fmg_api
            else:
                raise TypeError("CLASS ModelDevice: fmg_api param must be an object type "
                                "fntlib.fmg.jsonapi.FortiManagerJSON")

        if device != None and not isinstance(device, dict):
            raise TypeError("CLASS ModelDevice: 'device' param when passed, must be type 'dict'")
        # Add values from device dictionary to self if they exist in dictionary, otherwise set to None
        self.adom = device['adom'] if 'adom' in device else None
        self.vdom = device['vdom'] if 'vdom' in device else None
        self.user = device['user'] if 'user' in device else None
        self.password = device['password'] if 'password' in device else None
        self.descr = device['descr'] if 'descr' in device else None
        self.name = device['name'] if 'name' in device else None
        self.serial_num = device['serial_num'] if 'serial_num' in device else None
        self.meta_vars = device['meta_vars'] if 'meta_vars' in device else None
        self.platform = device['platform'] if 'platform' in device else None
        self.policy_package = device['policy_package'] if 'policy_package' in device else None
        self.preferred_img = device['preferred_img'] if 'preferred_img' in device else None
        self.group = device['group'] if 'group' in device else None
        self.sdwan_template = device['sdwan_template'] if 'sdwan_template' in device else None
        self.pre_cli_template = device['pre_cli_template'] if 'pre_cli_template' in device else None
        self.template_group = device['template_group'] if 'template_group' in device else None


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
        namexist = self.check_dev_name_in_fmg()
        serialexist = self.check_dev_sn_in_fmg()

        if namexist and serialexist:
            same = self.check_exist_dev_name_and_sn_same()
            if same == False:
                raise('Error: \"name\" and \"sn\" both exist in FMG DVM and are not associated to same object')
            else:
                return True

        url = 'dvm/cmd/add/device'
        data = {
            "adom": self.adom,
            "flags": ["create_task",
                      "nonblocking"],
            "device": {
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


    # Function to assign model device to pre-run CLI template
    def add_to_pre_cli_script(self):
        url = f'/pm/config/adom/{self.adom}/obj/cli/template/{self.pre_cli_template}/scope member'
        data = {
            "name": self.name,
            "vdom": 'global'  # Must set this to global, not sure why...
        }
        response = self.api.add(url, data)
        return self.__api_result(response)

    # Function to quick install settings for device to device DB (for pre-run cli template assign)
    def install_device_db(self):
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
        url = f'/dvmdb/adom/{self.adom}/group/{self.group}/object member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        response = self.api.add(url, data)
        return self.__api_result(response)


    # Function to add device to sdwan template
    def add_to_sdwan_templ(self):
        url = f'/pm/wanprof/adom/{self.adom}/{self.sdwan_template}/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        response = self.api.add(url, data)
        return self.__api_result(response)

    # Function to add device to CLI template group
    def add_to_cli_templ_group(self):
        url = f'/pm/config/adom/{self.adom}/obj/cli/template-group/{self.template_group}/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        response = self.api.add(url, data)
        return self.__api_result(response)

    # Function to add device to policy package
    def add_to_pol_pkg(self):
        url = f'/pm/pkg/adom/root/fwpol_branches/scope member'
        data = {
            "name": self.name,
            "vdom": self.vdom
        }
        response = self.api.add(url, data)
        return self.__api_result(response)


    # Function to install previously assigned policy package to policy DB
    def install_pol_pkg_to_db(self):
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
        url = "dvmdb/device/"
        data = {
            'filter': [
                ['name', '==', self.name]
            ],
            'fields': ['sn']
        }
        response = self.api.get(url,data)
        return True if response[1][0]['sn'] == self.serial_num else False

