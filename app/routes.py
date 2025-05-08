from flask import Blueprint, request, jsonify, render_template
from app_config import AppConfig
from .commands import BGPLookingGlass
import logging

# Configure logging
logging.basicConfig(level=AppConfig.LOG_LEVEL, format=AppConfig.LOG_FORMAT)

bp = Blueprint('main', __name__)
commands = BGPLookingGlass()

@bp.route('/')
def index():
    return render_template('index.html', devices=commands.devices['devices'])

@bp.route('/get_allowed_commands')
def get_allowed_commands():
    device = request.args.get('device')
    logging.debug(f"Fetching allowed commands for device: {device}")
    if not device:
        return jsonify({'error': 'Device parameter is required'}), 400
    device_config = next((d for d in commands.devices['devices'] if d['name'] == device), None)
    if not device_config:
        return jsonify({'error': 'Device not found'}), 404
    allowed_commands = commands.commands['commands']
    device_allowed = device_config.get('allowed_commands', [])
    device_disallowed = device_config.get('disallowed_commands', [])
    filtered_commands = {k: v for k, v in allowed_commands.items() if k in device_allowed and k not in device_disallowed}
    return jsonify({'commands': filtered_commands})

@bp.route('/get_variables')
def get_variables():
    command = request.args.get('command')
    if not command:
        return jsonify({'error': 'Command parameter is required'}), 400
    command_config = commands.commands['commands'].get(command)
    if not command_config:
        return jsonify({'error': 'Command not found'}), 404
    return jsonify({'variables': command_config.get('variables', [])})

@bp.route('/execute', methods=['POST'])
def execute():
    form_data = request.form.to_dict()
    device = form_data.get('device')
    command = form_data.get('command')
    if not device or not command:
        return jsonify({'error': 'Missing required parameters: device and command'}), 400

    # Process variables
    variables = {k: v for k, v in form_data.items() if k.startswith('variables[')}
    logging.debug(f"Form variables processed: {variables}")

    result = commands.get_device_output(device, command, variables)
    if 'error' in result:
        return jsonify({'error': result['error']})
    
    # Return the output directly from the result
    output = result.get('output', '')
    logging.debug(f"Returning output to UI: {output}")
    return jsonify({'output': output})

@bp.route('/api')
def api_docs():
    return render_template('api.html')

@bp.route('/api/execute', methods=['POST'])
def api_execute():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    device = data.get('device')
    command = data.get('command')
    if not device or not command:
        return jsonify({'error': 'Missing required parameters: device and command'}), 400

    # Process variables if provided
    variables = data.get('variables', {})
    logging.debug(f"API variables processed: {variables}")

    result = commands.get_device_output(device, command, variables)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    # Return the raw output as JSON
    output = result.get('output', '')
    logging.debug(f"Returning API output: {output}")
    return jsonify({'result': output})
