from napalm import get_network_driver
import yaml
import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BGPLookingGlass:
    def __init__(self):
        self.devices_config = self.load_config('devices.yaml')
        self.commands = self.load_config('commands.yaml')
        self.devices = self.process_devices()

    def load_config(self, filename):
        with open(os.path.join('app/config', filename), 'r') as f:
            return yaml.safe_load(f)

    def process_devices(self):
        devices = []
        groups = self.devices_config.get('groups', {})
        for device in self.devices_config.get('devices', []):
            group_name = device.get('group', 'ungrouped')
            device_settings = device.copy()
            device_settings['group'] = group_name

            device_allowed_commands = device.get('allowed_commands', [])

            if group_name in groups:
                group_settings = groups[group_name].copy()
                group_allowed_commands = group_settings.get('allowed_commands', [])
                combined_commands = list(set(group_allowed_commands + device_allowed_commands))
                for key, value in device.items():
                    group_settings[key] = value
                group_settings['group'] = group_name
                group_settings['allowed_commands'] = combined_commands
                devices.append(group_settings)
            else:
                device_settings['allowed_commands'] = device_allowed_commands
                devices.append(device_settings)
        logging.debug(f"Processed devices: {[d['name'] for d in devices]}")
        return {'devices': devices}

    def validate_variables(self, command_name, variables):
        command_config = self.commands['commands'].get(command_name, {})
        for var in command_config.get('variables', []):
            var_name = var['name']
            regex = var.get('regex')
            if var_name in variables and regex:
                if not re.match(regex, variables[var_name]):
                    return False, f"Invalid input for {var_name}"
        return True, None

    def get_device_output(self, device_name, command_name, variables=None):
        logging.debug(f"Looking for device: {device_name}")
        logging.debug(f"Available devices: {[d['name'] for d in self.devices['devices']]}")
        device_config = next((d for d in self.devices['devices'] if d['name'] == device_name), None)
        if not device_config:
            logging.error(f"Device not found: {device_name}")
            return {"error": "Device not found"}
        if command_name not in device_config.get('allowed_commands', []):
            logging.warning(f"Command not allowed: {command_name} for device {device_name}")
            return {"error": "Command not allowed"}

        command_config = self.commands['commands'].get(command_name)
        if not command_config:
            logging.error(f"Command not found: {command_name}")
            return {"error": "Command not found"}

        if variables:
            valid, error = self.validate_variables(command_name, variables)
            if not valid:
                logging.error(f"Validation error: {error}")
                return {"error": error}

        command = command_config['command']
        if variables:
            try:
                command = command.format(**variables)
            except KeyError:
                logging.error("Invalid variables provided")
                return {"error": "Invalid variables"}

        try:
            driver = get_network_driver(device_config['driver'])
            with driver(
                hostname=device_config['hostname'],
                username=device_config['username'],
                password=device_config['password']
            ) as device:
                output = device.cli([command])
                logging.debug(f"Command output: {output[command]}")
                return {"output": output[command]}
        except Exception as e:
            logging.error(f"Error executing command: {str(e)}")
            return {"error": str(e)}
