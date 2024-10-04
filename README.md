# add_model_device

## Env Setup
These scripts/modules have been tested with python 3.10.12.  The package can be cloned from github with URL https://github.com/hyyperlite/fmg_model_device.git.  The required modules to be installed are listed in the "requirements.txt" file.

## Overview
This python script (add_model_device.py) and the associated python module implement a series of API options to provide a flexible and robust way to create model devices on Fortimanager for use in ZTP provisioning.

The script runs a series of optional API calls for the setup of the model device.  Each of the following steps may or may not be required for any given deployment thus each of the following steps may or may not be used based on the specific requirements: 

- Creation of model device on FortiManager (add_model_device)
- Assigning of target FortiOS version for model device (add_model_device)
- Assignment of model_device to device_group(s)  (add_to_dev_group) 
- Assigning of metadata variables for the model device (add_meta_vars_map)
- Assigning of "Pre Run CLI Template" to the model device (add_to_pre_cli)
- Install of "pre-cli" configuration to device DB for the model device (install_device_db_pre]
- Assigning of CLI template group (add_to_cli_templ_group)
- Assigning of GUI templates group (add_to_templ_group)
- Assigning of SDWAN template (add_to_sdwan_templ)
- Install of template configurations device db for model device (install_device_db_post)
- Assignment of policy package to model device (add_to_pol_pkg)
- Installation of policy package to device DB for model device (install_pol_pkg_to_db)

In addition to the above key functions for model device provisioning the add_model_device.py also provides a few other useful options:
'
- **get_device_info**: check if the current device being configured by script already exists in DB and return info about the existing device.  Also used to optionally prevent further provisioning of the device if it already exists in some form on the Fortimanager.  Checks for both overlapping device name and overlapping device serial number.
- **delete_device**: optionally if the device already exists on Fortimanager the device could be deleted before adding with model_device.  This is useful when doing testing such that you do not need to manually remove the device from Fortimanager prior to each test run while developing your ZTP process.
- **"ignore_dev_exists"** This parameter controls the behavior of the above two options.  If ignore_dev_exists is set to False then if the device exists already on FortiManager the provsiong of this model device will be aborted otherwise the model_device creation will attempt to be completed anyway.  If combined with "delete_device" param set to true, then matching device on fmg will be deleted before continuing the model device provisioning.
- get_device_group_info:  If device exists can query fmg for device group info and return details.

## Device Details (yaml)
The add_model_device script accepts as an cli option the path to a device file containing all of the data necessary to provision one or more fg devices.  The device file should be in yaml format.  Below is an example file contents:

```(yaml)
fg1:
  adom: root
  vdom: root
  vdomenabled: false
  login: admin
  password: ********
  descr: "Added by model device API"
  serial_num: FGXXXXXXXXXXX1
  platform: FortiGate-600F
  preferred_img: 7.4.5
  group: "device group name to assign to"
  sdwan_template: "sd-wan gui template to assign to"
  pre_cli_template: "pre run cli template to assign to"
  cli_template_group: "cli template group to assign to"
  template_group: "gui template group to assign to"
  policy_package: "policy package to assign to"
  meta_vars:
    admintimeout: 480
    hostname: fg1
fg2:
  adom: root
  vdom: root
  vdomenabled: false
  login: admin
  password: ********
  descr: "Added by model device API"
  serial_num: FGXXXXXXXXXXX2
  platform: FortiGate-600F
  preferred_img: 7.4.5
  group: "device group name to assign to"
  sdwan_template: "sd-wan gui template to assign to"
  pre_cli_template: "pre run cli template to assign to"
  cli_template_group: "cli template group to assign to"
  template_group: "gui template group to assign to"
  policy_package: "policy package to assign to"
  meta_vars:
    admintimeout: 480
    hostname: fg2
```

## Script settings
All of the configurable options of this script can be passed as command line arguments at execution time.  Many options do not however need to be set because the have defaults. The settings and defaults are listed below, but can also easily be observed in the top of the add_model_device script under the ArgParse configuration.  These settings need to be passed only if overriding the defaults.  With the exception of --fmg_ip (fortimanager IP address) and --fmg_pass (and FortiManager login password).

**General Params**
- --fgt_yaml (default: fgt.yaml): Path to file containing FG device(s) provisioning details
- --fmg_ip (no default): IP address (or hostname) of FortiManager to provision devices on
- --fmg_login (default: admin): Username for API login to FMG
- --fmg_pass (no default): Password for API login to FMG
- --fmg_ver: (default: 744) Version of FMG. Used to check 7.2 api vs. 7.4 as there's some diff in api call.
- --api_debug (default: False): Set to True to enable API request/response details to console terminal
- --ignore_dev_exists (default: False) If true this will allow to delete existing device on FMG if name/serial_number matches a device being provisioned (aka in the fgt_yaml file)

**Optional Validations**
- --get_device_info (default: True):   If True check if device in fgt_yaml file exists on FMG, if so return details
- --get_device_group_info (default: False):   If True check if device in fgt_yaml file exists on FMG, if so return its group association details.
- --delete_device (default: False): If set to true, and get_device_info is True and device with same name or serial number exists, delete existing device on FMG before provisioning the current model device.


**Primary Parameters**
- --add_model_device (Default: True): Enable adding of model device.  All parameters below this point in this document require this to be True.
- -- add_meta_vars_map (Default: True): Enable adding metadata variables from the fgt_yaml file if defined in the file.

**Secondary Parameters**
- --add_to_pre_cli (default: True): If 'pre_cli_template' defined in the yaml file then this will assign the model device to the defined pre-cli template.
- --install_device_db_pre (default: True): If 'pre_cli_template' defined in the yamls file and completion of assigning model device to pre cli template, this will install the pre_cli_template rendered settings to the device DB for this model device.
- --add_to_cli_templ_group (default: True):  If 'cli_template_group' is assigned in the fgt yaml file, then assign the model device to the template group defined.
- --install_device_db_cli (default: True): If 'cli_templategroup' is assigned in the fgt yaml file and the add_to_cli_templ_group function was successful, then install the rendered template settings to the model device DB.
- --add_to_dev_group (default: True):  If 'group' defined in the fgt yaml file, then assign this mode device to the defined device group on FMG.
- --add_to_sdwan_templ: If 'sdwan_template' defined in the fgt yaml file, assign this model device to the defined SDWAN template on FMG.
- -- add_to_templ_group (default: False): If 'template_group' defined in the fgt yaml file then assign this model device to the defined GUI template group on FMG.
- --install_device_db_post (default: False): If gui templates are also enabled and defined then run install to model device DB to add configurations rendered from all GUI based templates.
- -- add_to_pol_pkg (default: False): If 'policy_package' defined in fgt yaml file then assign this model device to the defined policy package
- --install_pol_pkg_to_db (default: False): If 'policy_package' defined in fgt yaml file and assignment of policy package is succesful the install the policy package settings to the model device DB on FMG.
