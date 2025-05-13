#!/bin/bash

# Function to generate a secure Flask secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))" > /tmp/secret_key.txt
    if [ -s /tmp/secret_key.txt ]; then
        SECRET_KEY=$(cat /tmp/secret_key.txt)
        echo "Generated Flask secret key successfully."
    else
        echo "Failed to generate Flask secret key."
        exit 1
    fi
}

# Function to update app_config.py with the generated secret key
update_app_config() {
    APP_CONFIG_FILE="/opt/bgplookingglass/app_config.py"
    if [ -f "$APP_CONFIG_FILE" ]; then
        sudo sed -i "s/SECRET_KEY = 'your_secret_key_here'/SECRET_KEY = '$SECRET_KEY'/" "$APP_CONFIG_FILE" && echo "Updated app_config.py with new secret key successfully." || { echo "Failed to update app_config.py with new secret key."; exit 1; }
    else
        echo "app_config.py not found at $APP_CONFIG_FILE."
        exit 1
    fi
}

# Function to check and copy configuration files
copy_config_files() {
    DEVICES_SRC="/opt/bgplookingglass/app/config/sample-devices.yaml"
    DEVICES_DEST="/opt/bgplookingglass/app/config/devices.yaml"
    COMMANDS_SRC="/opt/bgplookingglass/app/config/sample-commands.yaml"
    COMMANDS_DEST="/opt/bgplookingglass/app/config/commands.yaml"

    if [ -f "$DEVICES_DEST" ]; then
        echo "devices.yaml already exists at $DEVICES_DEST."
    else
        sudo cp "$DEVICES_SRC" "$DEVICES_DEST" && echo "Copied sample-devices.yaml to devices.yaml successfully." || { echo "Failed to copy sample-devices.yaml to devices.yaml."; exit 1; }
    fi

    if [ -f "$COMMANDS_DEST" ]; then
        echo "commands.yaml already exists at $COMMANDS_DEST."
    else
        sudo cp "$COMMANDS_SRC" "$COMMANDS_DEST" && echo "Copied sample-commands.yaml to commands.yaml successfully." || { echo "Failed to copy sample-commands.yaml to commands.yaml."; exit 1; }
    fi
}

# Function to detect the package manager
detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        PACKAGE_MANAGER="apt"
        SYSTEM_TYPE="debian"
        echo "Detected apt package manager (Debian/Ubuntu-based system)."
    elif command -v dnf >/dev/null 2>&1; then
        PACKAGE_MANAGER="dnf"
        SYSTEM_TYPE="rhel"
        echo "Detected dnf package manager (RHEL/Fedora-based system)."
    elif command -v yum >/dev/null 2>&1; then
        PACKAGE_MANAGER="yum"
        SYSTEM_TYPE="rhel"
        echo "Detected yum package manager (Older RHEL/CentOS-based system)."
    else
        echo "Cannot detect a supported package manager (apt, dnf, or yum). Please install dependencies manually."
        exit 1
    fi
}

# Function to install dependencies based on package manager
install_dependencies() {
    case $PACKAGE_MANAGER in
        "apt")
            sudo apt update && echo "Apt update completed." || { echo "Apt update failed."; exit 1; }
            sudo apt install -y python3 python3-venv python3-dev git nginx && echo "Apt package installation completed." || { echo "Apt package installation failed."; exit 1; }
            sudo systemctl enable nginx && echo "Nginx enabled at startup." || { echo "Failed to enable Nginx at startup."; exit 1; }
            sudo systemctl start nginx && echo "Nginx started successfully." || { echo "Failed to start Nginx."; exit 1; }
            ;;
        "dnf")
            sudo dnf install -y python3 python3-devel git nginx && echo "Dnf package installation completed." || { echo "Dnf package installation failed."; exit 1; }
            sudo dnf install -y python3-pip python3-virtualenv && echo "Dnf python3-pip and virtualenv installation completed." || echo "python3-pip or virtualenv not available, assuming virtualenv is included in python3."
            sudo dnf install -y epel-release && echo "EPEL installation completed." || echo "EPEL installation failed or not needed."
            sudo systemctl enable nginx && echo "Nginx enabled at startup." || { echo "Failed to enable Nginx at startup."; exit 1; }
            sudo systemctl start nginx && echo "Nginx started successfully." || { echo "Failed to start Nginx."; exit 1; }
            ;;
        "yum")
            sudo yum install -y python3 python3-devel git nginx && echo "Yum package installation completed." || { echo "Yum package installation failed."; exit 1; }
            sudo yum install -y python3-pip python3-virtualenv && echo "Yum python3-pip and virtualenv installation completed." || echo "python3-pip or virtualenv not available, assuming virtualenv is included in python3."
            sudo yum install -y epel-release && echo "EPEL installation completed." || echo "EPEL installation failed or not needed."
            sudo systemctl enable nginx && echo "Nginx enabled at startup." || { echo "Failed to enable Nginx at startup."; exit 1; }
            sudo systemctl start nginx && echo "Nginx started successfully." || { echo "Failed to start Nginx."; exit 1; }
            ;;
        *)
            echo "Unsupported package manager. Please install dependencies manually."
            exit 1
            ;;
    esac
}

# Function to detect the active firewall system and check if it's running
detect_firewall() {
    echo "Detecting active firewall system..."
    if command -v firewall-cmd >/dev/null 2>&1; then
        if systemctl is-active --quiet firewalld; then
            FIREWALL="firewalld"
            FIREWALL_RUNNING="yes"
            echo "Detected firewalld as the active firewall and it is running."
        else
            FIREWALL="firewalld"
            FIREWALL_RUNNING="no"
            echo "Detected firewalld installed, but it is not running."
        fi
    elif command -v ufw >/dev/null 2>&1; then
        if ufw status 2>/dev/null | grep -q "active"; then
            FIREWALL="ufw"
            FIREWALL_RUNNING="yes"
            echo "Detected ufw as the active firewall and it is running."
        else
            FIREWALL="ufw"
            FIREWALL_RUNNING="no"
            echo "Detected ufw installed, but it is not running or inactive."
        fi
    elif command -v iptables >/dev/null 2>&1; then
        if iptables -L -n 2>/dev/null | grep -q "Chain"; then
            FIREWALL="iptables"
            FIREWALL_RUNNING="yes"
            echo "Detected iptables as the active firewall and it appears to be in use."
        else
            FIREWALL="iptables"
            FIREWALL_RUNNING="no"
            echo "Detected iptables installed, but no active rules or chains found."
        fi
    else
        FIREWALL="none"
        FIREWALL_RUNNING="no"
        echo "No supported firewall \(firewalld, ufw, or iptables\) detected. Assuming no firewall is configured or running."
    fi
}

# Function to open ports 80 and 443 based on the detected firewall and if it's running
open_ports() {
    if [ "$FIREWALL_RUNNING" == "no" ]; then
        echo "Firewall $FIREWALL is not running. Skipping port opening. Ensure ports 80 and 443 are accessible if a firewall is enabled later."
        return
    fi

    case $FIREWALL in
        "firewalld")
            echo "Opening ports 80 and 443 using firewalld..."
            sudo firewall-cmd --permanent --add-port=80/tcp && sudo firewall-cmd --permanent --add-port=443/tcp && sudo firewall-cmd --reload && echo "Ports 80 and 443 opened successfully with firewalld." || { echo "Failed to open ports with firewalld."; exit 1; }
            ;;
        "ufw")
            echo "Opening ports 80 and 443 using ufw..."
            sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && echo "Ports 80 and 443 opened successfully with ufw." || { echo "Failed to open ports with ufw."; exit 1; }
            ;;
        "iptables")
            echo "Opening ports 80 and 443 using iptables..."
            sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT && sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT && echo "Ports 80 and 443 opened successfully with iptables." || { echo "Failed to open ports with iptables."; exit 1; }
            if command -v iptables-save >/dev/null 2>&1; then
                sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null && echo "Iptables rules saved successfully." || echo "Warning: Could not save iptables rules automatically. Save manually if needed."
            fi
            ;;
        "none")
            echo "No firewall detected or configured. Skipping port opening. Ensure ports 80 and 443 are accessible if a firewall is later enabled."
            ;;
        *)
            echo "Unsupported firewall system. Please open ports 80 and 443 manually."
            exit 1
            ;;
    esac
}

# Function to verify if ports are open (optional check)
verify_ports() {
    if [ "$FIREWALL_RUNNING" == "no" ]; then
        echo "Firewall is not running, unable to verify port status. Check manually if needed."
        return
    fi

    echo "Verifying if ports 80 and 443 are open..."
    if [ "$FIREWALL" == "firewalld" ]; then
        firewall-cmd --list-ports | grep -E '80/tcp|443/tcp' && echo "Ports are open." || echo "Ports may not be open. Check firewall settings."
    elif [ "$FIREWALL" == "ufw" ]; then
        ufw status | grep -E '80|443' && echo "Ports are open." || echo "Ports may not be open. Check firewall settings."
    elif [ "$FIREWALL" == "iptables" ]; then
        iptables -L -n | grep -E '80|443' && echo "Ports are open." || echo "Ports may not be open. Check firewall settings."
    else
        echo "No firewall detected, unable to verify port status. Check manually if needed."
    fi
}

# Generate Flask secret key and update app_config.py
generate_secret_key
update_app_config

# Detect the package manager
detect_package_manager

# Install dependencies
install_dependencies

# Set up virtual environment and install requirements
python3 -m venv venv && echo "Virtual environment created successfully." || { echo "Failed to create virtual environment."; exit 1; }
source venv/bin/activate && echo "Virtual environment activated successfully." || { echo "Failed to activate virtual environment."; exit 1; }
pip install --upgrade pip && echo "Pip upgraded successfully." || echo "Failed to upgrade pip, continuing with current version."
pip install -r requirements.txt && echo "Requirements installation completed." || { echo "Requirements installation failed."; exit 1; }

# Create user and set permissions
id bgplookingglass >/dev/null 2>&1 || sudo adduser -r -s /bin/false bgplookingglass && echo "User bgplookingglass created successfully." || echo "User bgplookingglass already exists."
sudo usermod -s /bin/bash bgplookingglass && echo "User bgplookingglass shell updated successfully." || { echo "Failed to update user bgplookingglass shell."; exit 1; }
sudo chown -R bgplookingglass:bgplookingglass /opt/bgplookingglass && echo "Permissions set for /opt/bgplookingglass successfully." || { echo "Failed to set permissions for /opt/bgplookingglass."; exit 1; }

# Copy configuration files before starting the service
copy_config_files

# Create symlink for systemd service
sudo ln -s /opt/bgplookingglass/system_files/bgplookingglass.service /etc/systemd/system/bgplookingglass.service && echo "Systemd service symlink created successfully." || { echo "Failed to create systemd service symlink."; exit 1; }
sudo systemctl daemon-reload && echo "Systemd daemon reloaded successfully." || { echo "Failed to reload systemd daemon."; exit 1; }
sudo systemctl enable --now bgplookingglass && echo "Systemd service enabled and started successfully." || { echo "Failed to enable and start systemd service."; exit 1; }
sudo systemctl status bgplookingglass >/dev/null 2>&1 & wait $! && echo "Systemd service status checked successfully in background." || echo "Failed to check systemd service status in background."

# Set up SSL certificates
sudo mkdir -p /etc/ssl/private && echo "SSL private directory created successfully." || { echo "Failed to create SSL private directory."; exit 1; }
sudo chmod 700 /etc/ssl/private && echo "SSL private directory permissions set successfully." || { echo "Failed to set SSL private directory permissions."; exit 1; }
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/bgplookingglass.key -out /etc/ssl/certs/bgplookingglass.crt -batch && echo "SSL certificates generated successfully." || { echo "Failed to generate SSL certificates."; exit 1; }

# Configure Nginx based on system type
case $SYSTEM_TYPE in
    "debian")
        sudo ln -s /opt/bgplookingglass/system_files/bgplookingglass.conf /etc/nginx/sites-available/bgplookingglass && echo "Nginx config symlink created in sites-available successfully." || { echo "Failed to create Nginx config symlink in sites-available."; exit 1; }
        sudo ln -s /etc/nginx/sites-available/bgplookingglass /etc/nginx/sites-enabled/ && echo "Nginx config symlink enabled in sites-enabled successfully." || { echo "Failed to enable Nginx config symlink in sites-enabled."; exit 1; }
        ;;
    "rhel")
        sudo ln -s /opt/bgplookingglass/system_files/bgplookingglass.conf /etc/nginx/conf.d/bgplookingglass.conf && echo "Nginx config symlink created in conf.d successfully." || { echo "Failed to create Nginx config symlink in conf.d."; exit 1; }
        sudo cp system_files/nginx.conf /etc/nginx/nginx.conf && echo "Nginx main config copied successfully." || { echo "Failed to copy Nginx main config."; exit 1; }
        sudo setsebool -P httpd_can_network_connect 1 && echo "SELinux boolean set successfully." || { echo "Failed to set SELinux boolean."; exit 1; }
        ;;
    *)
        echo "Unsupported system type. Please configure Nginx manually."
        exit 1
        ;;
esac

# Test and apply Nginx configuration
sudo nginx -t && echo "Nginx configuration test passed." || { echo "Nginx configuration test failed."; exit 1; }
sudo systemctl reload nginx && echo "Nginx reloaded successfully." || { echo "Failed to reload Nginx."; exit 1; }

# Firewall configuration
echo "Starting firewall configuration for BGP Looking Glass..."
detect_firewall
open_ports
verify_ports
echo "Firewall setup complete."

echo "Setup complete."
