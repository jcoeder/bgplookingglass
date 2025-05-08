from napalm import get_network_driver
import yaml
import os
import re
from app_config import AppConfig
import logging

# Configure logging
logging.basicConfig(level=AppConfig.LOG_LEVEL, format=AppConfig.LOG_FORMAT)

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

        def get_group_settings(group_name, visited=None):
            """Recursively get settings for a group, merging with parent group settings."""
            if visited is None:
                visited = set()  # Track visited groups to prevent cycles
            if group_name in visited:
                logging.warning(f"Cycle detected in group hierarchy for group: {group_name}")
                return {}
            visited.add(group_name)

            if group_name not in groups:
                return {}

            group_data = groups[group_name].copy()
            parent_name = group_data.get('parent')
            if parent_name:
                parent_settings = get_group_settings(parent_name, visited)
                # Merge parent settings with current group, current group takes precedence
                for key, value in group_data.items():
                    if key in parent_settings and isinstance(value, list):
                        parent_settings[key] = list(set(parent_settings[key] + value))
                    else:
                        parent_settings[key] = value
                return parent_settings
            return group_data

        for device in self.devices_config.get('devices', []):
            group_name = device.get('group', 'ungrouped')
            device_settings = device.copy()
            device_settings['group'] = group_name

            device_allowed_commands = device.get('allowed_commands', [])
            device_disallowed_commands = device.get('disallowed_commands', [])

            if group_name in groups or group_name != 'ungrouped':
                group_settings = get_group_settings(group_name)
                if group_settings:
                    group_allowed_commands = group_settings.get('allowed_commands', [])
                    group_disallowed_commands = group_settings.get('disallowed_commands', [])
                    combined_allowed = list(set(group_allowed_commands + device_allowed_commands) - set(group_disallowed_commands + device_disallowed_commands))
                    for key, value in device.items():
                        group_settings[key] = value
                    group_settings['group'] = group_name
                    group_settings['allowed_commands'] = combined_allowed
                    group_settings['disallowed_commands'] = list(set(group_disallowed_commands + device_disallowed_commands))
                    devices.append(group_settings)
                else:
                    device_settings['allowed_commands'] = list(set(device_allowed_commands) - set(device_disallowed_commands))
                    device_settings['disallowed_commands'] = device_disallowed_commands
                    devices.append(device_settings)
            else:
                device_settings['allowed_commands'] = list(set(device_allowed_commands) - set(device_disallowed_commands))
                device_settings['disallowed_commands'] = device_disallowed_commands
                devices.append(device_settings)
        logging.debug(f"Processed devices: {[d['name'] for d in devices]}")
        return {'devices': devices}

    def validate_variables(self, command_name, variables):
        command_config = self.commands['commands'].get(command_name, {})
        for var in command_config.get('variables', []):
            var_name = var['name']
            if var_name not in variables or not variables[var_name]:
                if var.get('required', False):
                    logging.debug(f"Missing required variable: {var_name}")
                    return False, f"Missing required variable: {var_name}"
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
        if command_name in device_config.get('disallowed_commands', []):
            logging.warning(f"Command disallowed: {command_name} for device {device_name}")
            return {"error": "Command disallowed"}

        command_config = self.commands['commands'].get(command_name)
        if not command_config:
            logging.error(f"Command not found: {command_name}")
            return {"error": "Command not found"}

        if variables:
            # Handle both API (direct dict) and form data (variables[key])
            cleaned_variables = {}
            if any(k.startswith('variables[') for k in variables.keys()):
                cleaned_variables = {k.replace('variables[', '').replace(']', ''): v for k, v in variables.items() if k.startswith('variables[')}
            else:
                cleaned_variables = variables
            logging.debug(f"Cleaned variables for execution: {cleaned_variables}")
            valid, error = self.validate_variables(command_name, cleaned_variables)
            if not valid:
                logging.error(f"Validation error: {error}")
                return {"error": error}
        else:
            cleaned_variables = {}
            logging.debug("No variables provided")

        command = command_config['command']
        logging.debug(f"Original command: {command}")
        if cleaned_variables:
            try:
                formatted_command = command.format(**cleaned_variables)
                logging.debug(f"Formatted command: {formatted_command}")
                command = formatted_command
            except KeyError as e:
                logging.error(f"Variable substitution failed: missing or invalid variable {e}")
                return {"error": f"Missing or invalid variable: {e}"}
            except ValueError as e:
                logging.error(f"Command formatting error: {e}")
                return {"error": f"Command formatting error: {e}"}
        else:
            if '{' in command and '}' in command:
                logging.error(f"Command requires variables but none provided: {command}")
                return {"error": "Command requires variables but none provided"}

        try:
            driver = get_network_driver(device_config['driver'])
            with driver(
                hostname=device_config['hostname'],
                username=device_config['username'],
                password=device_config['password']
            ) as device:
                output = device.cli([command])
                logging.debug(f"Command output: {output}")
                # Ensure the output is a string, even if it's a dictionary or list
                if isinstance(output, dict):
                    # Extract the output for the specific command if it's a dictionary
                    output = output.get(command, str(output))
                elif isinstance(output, list):
                    output = "\n".join(output)
                return {"output": str(output)}
        except Exception as e:
            logging.error(f"Error executing command: {str(e)}")
            return {"error": str(e)}
