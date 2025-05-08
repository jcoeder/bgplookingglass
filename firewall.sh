#!/bin/bash

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
        # Check if iptables has any rules or chains active as a basic running check
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
        echo "No supported firewall (firewalld, ufw, or iptables) detected. Assuming no firewall is configured or running."
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
            sudo firewall-cmd --permanent --add-port=80/tcp
            sudo firewall-cmd --permanent --add-port=443/tcp
            sudo firewall-cmd --reload
            echo "Ports 80 and 443 opened successfully with firewalld."
            ;;
        "ufw")
            echo "Opening ports 80 and 443 using ufw..."
            sudo ufw allow 80/tcp
            sudo ufw allow 443/tcp
            echo "Ports 80 and 443 opened successfully with ufw."
            ;;
        "iptables")
            echo "Opening ports 80 and 443 using iptables..."
            sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
            sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
            # Save iptables rules (method varies by system)
            if command -v iptables-save >/dev/null 2>&1; then
                sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || echo "Warning: Could not save iptables rules automatically. Save manually if needed."
            fi
            echo "Ports 80 and 443 opened successfully with iptables. Ensure rules are saved for persistence."
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

# Main execution
echo "Starting firewall configuration for BGP Looking Glass..."
detect_firewall
open_ports
verify_ports
echo "Firewall setup complete."
