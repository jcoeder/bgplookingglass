#!/bin/bash

# Function to detect the package manager
detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        PACKAGE_MANAGER="apt"
        echo "Detected apt package manager (Debian/Ubuntu-based system)."
    elif command -v dnf >/dev/null 2>&1; then
        PACKAGE_MANAGER="dnf"
        echo "Detected dnf package manager (RHEL/Fedora-based system)."
    elif command -v yum >/dev/null 2>&1; then
        PACKAGE_MANAGER="yum"
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
            sudo apt update
            sudo apt install -y python3 python3-venv python3-dev git nginx
            ;;
        "dnf")
            sudo dnf install -y python3 python3-devel git nginx
            sudo dnf install -y python3-venv || echo "python3-venv not available, assuming it's included in python3."
            # Enable EPEL for additional packages if needed
            sudo dnf install -y epel-release || echo "EPEL installation failed or not needed."
            ;;
        "yum")
            sudo yum install -y python3 python3-devel git nginx
            sudo yum install -y python3-venv || echo "python3-venv not available, assuming it's included in python3."
            # Enable EPEL for additional packages if needed
            sudo yum install -y epel-release || echo "EPEL installation failed or not needed."
            ;;
        *)
            echo "Unsupported package manager. Please install dependencies manually."
            exit 1
            ;;
    esac
}

# Detect the package manager
detect_package_manager

# Install dependencies
install_dependencies

# Set up virtual environment and install requirements
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Setup complete. Configure .env and Nginx before running."

