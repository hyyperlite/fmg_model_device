import csv
import yaml
import os
import json
from pathlib import Path
import argparse

CONFIG_FILE = Path.home() / ".fmg_model_device_converter_config.json"

def load_defaults():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "descr": "added fmg_model_device",
        "platform": "FortiGate-VM64-KVM",
        "preferred_img": "",
        "group": "",
        "adom": "root",
        "vdom": "root",
        "user": "admin",
        "password": "fortinet",
        "policy_package": "edge",
        "sdwan_template": "sdwan-edge",
        "pre_cli_template": "pre_vm_intfs",
        "cli_template_group": "cli_grp-Edge",
        "template_group": "edge",
    }

def save_defaults(defaults):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(defaults, f, indent=2)

def get_user_input(defaults, device_name):
    print(f"\nConfiguring device: {device_name}")
    manual_fields = {}
    for key, default_value in defaults.items():
        prompt = f"Enter value for '{key}' (default: {default_value if default_value else 'not set'}): "
        value = input(prompt).strip()
        if not value:
            value = default_value
        
        if value.lower() == 'none':
            manual_fields[key] = None
        else:
            manual_fields[key] = value
            defaults[key] = value # Remember for next device
    return manual_fields

def main():
    parser = argparse.ArgumentParser(
        description="Convert a CSV file of FortiManager device blueprints to YAML files.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Example usage:
  - To convert a CSV into multiple YAML files (default behavior):
    python convert_csv_to_yaml.py my_devices.csv

  - To convert a CSV into a single combined YAML file:
    python convert_csv_to_yaml.py my_devices.csv --output-mode single --output-name combined_devices.yml

CSV to YAML Mapping:
  - "Name"           -> top-level key, and 'name' field (required)
  - "Serial Number"  -> 'serial_num' field (required)
  - "Device Blueprint" -> 'blueprint' field (optional)
  - Other CSV columns will be added to the 'meta_vars' dictionary in the YAML.

The script will interactively prompt for the following fields for each device,
with defaults that are remembered across runs:
  - descr
  - platform
  - preferred_img
  - group
  - adom
  - vdom
  - user
  - password
  - policy_package
  - sdwan_template
  - pre_cli_template
  - cli_template_group
  - template_group
"""
    )
    parser.add_argument("csv_file", help="Path to the input CSV file.")
    parser.add_argument(
        "--output-mode",
        choices=["single", "multiple"],
        default="multiple",
        help="Output to a single combined file or multiple individual files. Default: multiple."
    )
    parser.add_argument(
        "--output-name",
        default="output.yml",
        help="The name of the output file when using 'single' output mode. Default: output.yml"
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="The directory to save the output YAML files. Default: data/"
    )
    
    args = parser.parse_args()

    csv_file_path = args.csv_file
    if not os.path.exists(csv_file_path):
        print(f"Error: File not found at '{csv_file_path}'")
        return

    output_option = args.output_mode
    output_filename = ""
    if output_option == "single":
        output_filename_input = args.output_name
        if not output_filename_input.endswith(('.yml', '.yaml')):
            output_filename_input += '.yml'
    
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    if output_option == "single":
        output_filename = os.path.join(output_dir, output_filename_input)


    defaults = load_defaults()
    all_yaml_data = {}

    with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        rows = list(reader)
        if not rows:
            print("CSV file is empty.")
            return

        for row in rows:
            device_name = row.get("Name")
            if not device_name:
                print("Skipping row due to missing 'Name' field.")
                continue

            yaml_data = {
                device_name: {
                    "name": device_name,
                    "serial_num": row.get("Serial Number"),
                }
            }

            if "Device Blueprint" in row and row["Device Blueprint"]:
                yaml_data[device_name]["blueprint"] = row["Device Blueprint"]

            manual_inputs = get_user_input(defaults, device_name)
            for key, value in manual_inputs.items():
                if value is not None:
                    yaml_data[device_name][key] = value

            meta_vars = {}
            predefined_keys = ["Name", "Serial Number", "Device Blueprint"]
            for key, value in row.items():
                if key not in predefined_keys and value:
                    meta_vars[key] = value
            
            if meta_vars:
                yaml_data[device_name]["meta_vars"] = meta_vars

            if output_option == "multiple":
                single_output_filename = os.path.join(output_dir, f"{device_name}.yml")
                with open(single_output_filename, 'w') as yaml_file:
                    yaml.dump(yaml_data, yaml_file, default_flow_style=False, sort_keys=False)
                print(f"Successfully created {single_output_filename}")
            else: # single file
                all_yaml_data.update(yaml_data)

    if output_option == "single":
        with open(output_filename, 'w') as yaml_file:
            yaml.dump(all_yaml_data, yaml_file, default_flow_style=False, sort_keys=False)
        print(f"Successfully created combined file {output_filename}")

    save_defaults(defaults)
    print("\nConversion complete.")

if __name__ == "__main__":
    main()
