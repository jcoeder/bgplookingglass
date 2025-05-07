from flask import Blueprint, render_template, request, jsonify
from .bgp import BGPLookingGlass
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

bp = Blueprint('main', __name__)
bgp = BGPLookingGlass()

@bp.route('/')
def index():
    return render_template('index.html', devices=bgp.devices['devices'], commands=bgp.commands['commands'])

@bp.route('/get_allowed_commands')
def get_allowed_commands():
    device_name = request.args.get('device')
    logging.debug(f"Fetching allowed commands for device: {device_name}")
    device_config = next((d for d in bgp.devices['devices'] if d['name'] == device_name), None)
    if not device_config:
        logging.error(f"Device not found in get_allowed_commands: {device_name}")
        return jsonify({'error': 'Device not found'})
    allowed_commands = device_config.get('allowed_commands', [])
    filtered_commands = {k: v for k, v in bgp.commands['commands'].items() if k in allowed_commands}
    return jsonify({'commands': filtered_commands})

@bp.route('/get_variables')
def get_variables():
    command = request.args.get('command')
    command_config = bgp.commands['commands'].get(command, {})
    return jsonify({'variables': command_config.get('variables', [])})

@bp.route('/execute', methods=['POST'])
def execute():
    device = request.form.get('device')
    command = request.form.get('command')
    logging.debug(f"Executing command: {command} on device: {device}")
    variables = {}

    command_config = bgp.commands['commands'].get(command, {})
    for var in command_config.get('variables', []):
        value = request.form.get(var['name'])
        if value:
            variables[var['name']] = value

    result = bgp.get_device_output(device, command, variables)
    return jsonify(result)
