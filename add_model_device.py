#! /usr/bin/python

"""
Created by: Nick Petersen, Fortinet CSE - Americas

Script to add Model Devices to FortiManager
Optionally can do all of the following (and does by default)
1. Add model device (ID by Serial Number) to DVM (including meta data variables)
2. Add pre-run CLI template to device
3. "Quick-install" to Device Database (to update DB from pre-run template)
4.  Add model device to device group
5.  Add model device to SDWAN template
6.  Add model device to CLI Template Group
7.  "Quick install" to Device Database (to execute post-run templates)
8.  Add device as install target on target FW pol pkg (not required due to groups, but preferred when on GUI)
9.  Install policy package and device settings to FMG DB
10. Done  (now wait to device with matching details to attempt registration with FMG)

Notes:
    -  Model device is finicky, this is why I install device DB (locally) twice and then install devdb
       plus policy pkg.

    -  Make sure you have your "fg_platform" setting right.  If its KVM you need "FortiGate-VM64-KVM" not
       just "FortiGate-VM64".  If you don't have this right, it will fail when upgrading to the
       "fg_preferred_img"

    - If things aren't installing correct once the real device is registered; ensure that your login
      password is correct.   For brand new (Fortideploy, etc) devices the password should be "".  For
      devices you are testing with but not completely factory resetting, this will be the set password.
"""

# Adding model device and configuring it for first time deployment
from ftntlib import FortiManagerJSON
from modeldevice import ModelDevice
import argparse
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--fgt_yaml', default='devices.yml')
parser.add_argument('--fmg_ip', default='10.99.227.120')
parser.add_argument('--fmg_login', default='admin')
parser.add_argument('--fmg_pass', default='fortinet')
parser.add_argument('--debug', type=bool,  default=False)
parser.add_argument('--verbose', type=bool, default=False)

# Enable/Disable specific components
parser.add_argument('--add_model_device', type=bool, default=True)
parser.add_argument('--add_to_pre_cli', type=bool, default=True)
parser.add_argument('--install_device_db_pre', type=bool, default=True)
parser.add_argument('--add_to_dev_group', type=bool, default=True)
parser.add_argument('--add_to_sdwan_templ', type=bool, default=True)
parser.add_argument('--add_to_cli_templ_group', type=bool, default=True)
parser.add_argument('--install_device_db_post', type=bool, default=True)
parser.add_argument('--add_to_pol_pkg', type=bool, default=True)
parser.add_argument('--install_pol_pkg_to_db', type=bool, default=True)
args = parser.parse_args()

# Instantiate and Login to Fortimanager
api = FortiManagerJSON()
api.verbose('on') if args.verbose else api.verbose('off')
api.debug('on') if args.debug else api.debug('off')
api.login(args.fmg_ip, args.fmg_login, args.fmg_pass)

# Open YAML file containing model_device information
with open(args.fgt_yaml) as file:
    # load from yaml file to dict
    devices = yaml.load(file)
    for fg in devices:
        print(f'### Processing {fg}')
        # Create class instance of ModelDevice for this fg device to be added
        # We provide the device info as 'dict' and the logged in fntlib api
        md = ModelDevice(devices[fg], api)

        # Add model device to FMG
        if args.add_model_device:
            print(f'  Adding model device {fg} to fmg:', end=' ')
            result = md.add()
            print('Success') if result else print('Failed')

        # Add model device (already in DVM) to pre-run cli template
        if args.add_to_pre_cli:
            print(f'  Adding model device {fg} to pre-run CLI template \"'
                  f'{devices[fg]["pre_cli_template"]}\" :', end=' ')
            result = md.add_to_pre_cli_script()
            print('Success') if result else print('Failed')\

        # Install Device Settings (Quick DB Install)
        if args.install_device_db_pre:
            print(f'  Install (Quick Install) to Device DB for pre-run CLI template :', end=' ')
            result = md.install_device_db()
            print('Success') if result else print('Failed')\

        # Add device to DVM Group
        if args.add_to_dev_group:
            print(f'  Add {fg} to FMG Device Group \"{devices[fg]["group"]}\" :', end=' ')
            result = md.add_to_dev_group()
            print('Success') if result else print('Failed')

        # Add device to SDWAN Template
        if args.add_to_sdwan_templ:
            print(f'  Add {fg} to SDWAN Template \"{devices[fg]["sdwan_template"]}\" :', end=' ')
            result = md.add_to_sdwan_templ()
            print('Success') if result else print('Failed')

        # Assign model device to post-run CLI template group
        if args.add_to_cli_templ_group:
            print(f'  Add {fg} to CLI Template Group \"{devices[fg]["template_group"]}\" :', end=' ')
            result = md.add_to_cli_templ_group()
            print('Success') if result else print('Failed')

        # Install Device Settings again, this time to add post run templates to DB
        if args.install_device_db_post:
            print(f'  Install (Quick Install) to Device DB for post-run CLI template/group :', end=' ')
            result = md.install_device_db()
            print('Success') if result else print('Failed')

        # Assign model device to a policy package (not totally needed with being in group, but prefer indiv option)
        if args.add_to_pol_pkg:
            print(f'  Add {fg} to Policy Package \"{devices[fg]["policy_package"]}\" :', end=' ')
            result = md.add_to_pol_pkg()
            print('Success') if result else print('Failed')

        # Install Device Settings (hopefully this is quick DB install?)
        if args.install_pol_pkg_to_db:
            print(f'  Install to DB Policy Package for device :', end=' ')
            result = md.install_pol_pkg_to_db()
            print('Success') if result else print('Failed')

api.logout()
