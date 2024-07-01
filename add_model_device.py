#! /usr/bin/python

"""
Created by: Nick Petersen, Fortinet CSE - Americas

Script to add Model Devices to FortiManager
Optionally can do any of the following (and does by default)
1. Add model device (ID by Serial Number) to DVM (including metadata variables)
2. Add pre-run CLI template to device
3. "Quick-install" to Device Database (to update DB from pre-run template)
4.  Add model device to device group
5.  Add model device to SDWAN template
6.  Add model device to CLI Template Group
7.  Add model device to "Template Group"  (not CLI template group)
8.  "Quick install" to Device Database (to execute post-run templates)
9.  Add device as install target on target FW pol pkg (not required due to groups, but preferred when on GUI)
10.  Install policy package and device settings to FMG DB
11. Done  (now wait to device with matching details to attempt registration with FMG)

Notes:
    -  Model device is finicky, this is why I install device DB (locally) twice and then install devdb
       plus policy pkg.

    -  Make sure you have your "fg_platform" setting right.  If its KVM you need "FortiGate-VM64-KVM" not
       just "FortiGate-VM64".  If you don't have this right, it will fail when upgrading to the
       "fg_preferred_img"

    - If things aren't installing correctly once the real device is registered; ensure that your login
      password is correct.   For brand new (Fortideploy, etc) devices the password should be "".  For
      devices you are testing with but not completely factory resetting, this will be the current device password.
"""

# Adding model device and configuring it for first time deployment
from pyFMG.fortimgr import *
from modeldevice import *
import argparse
import yaml
import sys
import urllib3
from pprint import pprint

urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument('--fgt_yaml', default='fgt.yml')
parser.add_argument('--fmg_ip')
parser.add_argument('--fmg_login', default='admin')
parser.add_argument('--fmg_pass')
parser.add_argument('--fmg_ver', type=int, default=720)
parser.add_argument('--api_debug', type=bool,  default=False)
parser.add_argument('--ignore_dev_exists', type=bool, default=False)

# Some testing/checking options
parser.add_argument('--get_device_info', type=bool, default=False)
parser.add_argument('--get_device_group_info', type=bool, default=False)
parser.add_argument('--delete_device', type=bool, default=False)
parser.add_argument('--check_fmg_script', type=bool, default=False)

# Enable/Disable components for use with fmg 7.2+ features (blueprint and/or new metavars)
parser.add_argument('--add_model_device', type=bool, default=True)
parser.add_argument('--add_meta_vars_map', type=bool, default=True)
#parser.add_argument('--use_device_blueprint', type=bool, default=True) #no longer working

# Additional processing
parser.add_argument('--add_to_pre_cli', type=bool, default=True)
parser.add_argument('--install_device_db_pre', type=bool, default=True)
parser.add_argument('--add_to_cli_templ_group', type=bool, default=True)
parser.add_argument('--install_device_db_cli', type=bool, default=True)
parser.add_argument('--add_to_dev_group', type=bool, default=True)
parser.add_argument('--add_to_sdwan_templ', type=bool, default=True)
parser.add_argument('--add_to_templ_group', type=bool, default=False)
parser.add_argument('--install_device_db_post', type=bool, default=True)
parser.add_argument('--add_to_pol_pkg', type=bool, default=False)
parser.add_argument('--install_pol_pkg_to_db', type=bool, default=False)
args = parser.parse_args()

# Instantiate and Login to Fortimanager
# api = pyfgt.fortimgr instance
api = FortiManager(args.fmg_ip, args.fmg_login, args.fmg_pass, debug=args.api_debug, timeout=30, verify_ssl=False)


def check_result(md_code, md_msg):
    if md_msg == 'ABORT':
        md_msg = '!!! Aborting configuration of this device.'

    if md_code == 0:
        print('Success')
        return True
    else:
        print(f'Failed: {md_msg}')
        return False


# Try to open HTTP(s)/JSON API connection to FMG
try:
    api.login()
except FMGConnectionError:
    print(f'Unable to reach/login to FMG at {args.fmg_ip}, aborting.')
    sys.exit()
except FMGValidSessionException:
    print(f'Unable to reach/login to FMG at {args.fmg_ip}, aborting.')
    sys.exit()
else:
    print(f'Successfully connected to FMG {args.fmg_ip} API\n')

# Open YAML file containing model_device information
try:
    f = open(args.fgt_yaml)
except FileNotFoundError:
    print(f'!!! Cannot find device yaml file at {args.fgt_yaml}, aborting !!!')
    sys.exit()
else:
    # load from yaml file to dict
    devices = yaml.safe_load(f)
    f.close()

for fg in devices:
    print(f'<<<< Processing device: {fg} >>>>')
    # Create class instance of ModelDevice for this fg device to be added
    # We provide the device info as 'dict' and the logged in fntlib api
    devices[fg]['name'] = fg   # assign name of device as var in dict
    md = ModelDevice(devices[fg], api, args.fmg_ver)

    if args.get_device_info:
        print(f'  Get/print info for device {fg} if exists')
        md.get_device_info()
        #pprint(md.get_device_info())
        sys.exit()

    if args.get_device_group_info:
        print(f'   Get/print group info')
        pprint(md.get_dev_group_info())
        sys.exit()

    if args.delete_device:
        print(f' Delete device: ', end='')
        code, msg = md.delete()
        check_result(code, msg)

    if args.check_fmg_script:
        print(f' Checking if script: {devices[fg]["fmg_script"]} exists')
        pprint(md.check_fmg_script())

    # Add model device to FMG
    if args.add_model_device:
        print(f'  Adding model device {fg}: ', end=' ')
        try:
            code, msg = md.add()
        # Catch exception from ModelDevice for if the sn or name already exists in FMG DVM and then handle
        except MdFmgDvmError as e:
            if args.ignore_dev_exists:
                print(f'\n    {e}, Continuing with configurations due to "ignore_dev_exists" flag set')
            else:
                print(f'\n    {e}, Abort further configuration of this device')
                continue
        # Catch exception from ModelDevice for if not enough variables provided to add device
        except MdDataError as e:
            print(f'\n    {e}, Aborting further configuration of this device')
            continue
        # No exceptions, so continue as normal
        else:
            if not check_result(code, 'ABORT'):
                continue

    if args.add_meta_vars_map and args.fmg_ver >= 720:
        print(f'  Adding metadata variable mappings: ', end=' ')
        code, msg = md.add_fmg_meta_vars_mapping()
        if not check_result(code, 'ABORT'):
            continue

    # Add model device (already in DVM) to pre-run cli template
    if args.add_to_pre_cli:
        if 'pre_cli_template' in devices[fg]:
            if devices[fg]['pre_cli_template'].lower() != 'none':
                print(f'  Adding {fg} to pre-run CLI template \"'
                        f'{devices[fg]["pre_cli_template"]}\": ', end=' ')
                code, msg = md.add_to_pre_cli_script()
                if not check_result(code, 'ABORT'):
                    continue

    # Install Device Settings (Quick DB Install)
    if args.install_device_db_pre:
        print(f'  Install (Quick Install) to Device DB for pre-run CLI template: ', end=' ')
        code, msg = md.install_device_db()
        if not check_result(code, 'ABORT'):
            continue

    # Assign model device to post-run CLI template group
    if args.add_to_cli_templ_group:
        print(f'  Add {fg} to CLI Template Group \"{devices[fg]["cli_template_group"]}\": ', end=' ')
        code, msg = md.add_to_cli_templ_group()
        if not check_result(code, 'ABORT'):
            continue

    # Install Device Settings (Quick DB Install)
    if args.install_device_db_cli:
        print(f'  Install (Quick Install) to Device DB for post-run CLI templates: ', end=' ')
        code, msg = md.install_device_db()
        if not check_result(code, 'ABORT'):
            continue

    # Add device to DVM Group
    if args.add_to_dev_group:
        print(f'  Add {fg} to FMG Device Group \"{devices[fg]["group"]}\": ', end=' ')
        code, msg = md.add_to_dev_group()
        if not check_result(code, 'ABORT'):
            continue

    # Add device to SDWAN Template
    if args.add_to_sdwan_templ:
        if 'sdwan_template' in devices[fg]:
            if devices[fg]['sdwan_template'].lower() != 'none':
                if "sdwan_template" in devices[fg]:
                    print(f'  Add {fg} to SDWAN Template \"{devices[fg]["sdwan_template"]}\": ', end=' ')
                    code, msg = md.add_to_sdwan_templ()
                    if not check_result(code, 'ABORT'):
                        continue
                else:
                    print(f'  sdwan_template parameter not provided, skipping add to sdwan-template')

    # Assign model device to general template groups (not cli)
    if args.add_to_templ_group:
        print(f'  Add {fg} to Template Group \"{devices[fg]["template_group"]}\": ', end=' ')
        code, msg = md.add_to_templ_group()
        if not check_result(code, 'ABORT'):
            continue

    # Install Device Settings again, this time to add post run templates to DB
    if args.install_device_db_post:
        print(f'  Install (Quick Install) to Device DB for post-run CLI template/group: ', end=' ')
        code, msg = md.install_device_db()
        if not check_result(code, 'ABORT'):
            continue

    # Assign model device to a policy package (not totally needed with being in group, but prefer indiv option)
    if args.add_to_pol_pkg:
        print(f'  Add {fg} to Policy Package \"{devices[fg]["policy_package"]}\": ', end=' ')
        code, msg = md.add_to_pol_pkg()
        if not check_result(code, 'ABORT'):
            continue

    # Install Device Settings (hopefully this is quick DB install?)
    if args.install_pol_pkg_to_db:
        print(f'Install to DB Policy Package for device: ', end=' ')
        code, msg = md.install_pol_pkg_to_db()
        if not check_result(code, 'ABORT'):
            continue


api.logout()
