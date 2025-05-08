# Source: routes.py
# Published: 5/10/2025, 8:00:00 PM (updated)

from flask import Blueprint, render_template, request, jsonify
from .commands import BGPLookingGlass  # Import from the renamed file
import logging
import re

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
    device = None
    command = None
    variables = {}
    
    try:
        # Check for JSON data
        json_data = request.get_json(silent=True)
        if json_data:
            device = json_data.get('device')
            command = json_data.get('command')
            variables = json_data.get('variables', {})
            logging.debug(f"JSON variables received: {variables}")
        else:
            # Fall back to form data
            device = request.form.get('device')
            command = request.form.get('command')
            for key in request.form:
                if key == 'device' or key == 'command':
                    continue
                if match := re.match(r'variables\[(\w+)\]', key):
                    var_key = match.group(1)  # Extract 'host'
                    variables[var_key] = request.form.get(key)
                else:
                    variables[key] = request.form.get(key)
            logging.debug(f"Form variables processed: {variables}")
        
        if not device or not command:
            return jsonify({"error": "Missing required parameters: device and command"}), 400
        
        # Ensure variables is a dict of strings
        cleaned_variables = {k: str(v) for k, v in variables.items()}
        logging.debug(f"Cleaned variables for execution: {cleaned_variables}")
        
        result = bgp.get_device_output(device, command, cleaned_variables)
        if isinstance(result, dict) and len(result) > 0:
            output_string = next(iter(result.values()))  # Extract the string output
            return jsonify({"output": output_string})
        else:
            return jsonify({"error": "No output from device"}), 400
    except Exception as e:
        logging.error(f"Error in /execute: {str(e)} - Variables: {variables}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Updated /api endpoint to display example curl commands with "show_bgp_summary"
@bp.route('/api', methods=['GET'])
def api_examples():
    if request.method == 'GET':
        return """
        <html>
        <head>
            <title>BGP API Examples</title>
        </head>
        <body>
            <h1>BGP Looking Glass API Examples</h1>
            <p>Use the following curl commands to interact with the /execute endpoint:</p>
            <ul>
                <li><strong>Basic Example (Form Data):</strong> <code>curl -X POST http://172.30.16.44:8000/execute -H "Content-Type: application/x-www-form-urlencoded" -d "device=router1&command=show_bgp_summary"</code></li>
                <li><strong>Example with Variables (Form Data):</strong> <code>curl -X POST http://172.30.16.44:8000/execute -H "Content-Type: application/x-www-form-urlencoded" -d "device=router1&command=show_ip_bgp_prefix&variables[prefix]=192.0.2.0/24"</code></li>
                <li><strong>JSON Example:</strong> <code>curl -X POST http://172.30.16.44:8000/execute -H "Content-Type: application/json" -d '{"device": "router1", "command": "show_bgp_summary"}'</code></li>
            </ul>
            <p>Note: Replace 172.30.16.44 with your server's IP. Ensure the device and command are valid in your configuration.</p>
        </body>
        </html>
        """, 200, {'Content-Type': 'text/html'}
    else:
        return "Method not allowed. Use GET for this endpoint.", 405

