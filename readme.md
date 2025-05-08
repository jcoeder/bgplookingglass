# BGP Looking Glass

A Flask-based web application for executing network commands on configured devices and retrieving raw output in JSON format. This tool provides a user-friendly interface and API for BGP and network diagnostics.

The application uses NAPALM to connect to the network devices so the app shoud support and devices NAPALM supports.  By default this app ships with most of the commands for someone would want for Arista devices but its very easy to add additional commands

## Prerequisites

- A Linux-based system (RHEL 8/9 or Ubuntu 20.04/22.04 or later)
- Python 3.8 or higher
- Git
- Nginx
- Access to a user with sudo privileges for initial setup

## Setup Instructions

This guide will walk you through setting up the BGP Looking Glass app as a non-root user named `bgplookingglass`, installing it in `/opt/bgplookingglass`, and configuring it to run as a systemd service with Nginx as a reverse proxy. Instructions are provided for both RHEL and Ubuntu systems.

### Step 1: Clone the repository
```bash
cd /opt
git clone https://github.com/jcoeder/bgplookingglass
```

### Step 2: Install dependencies and setup the environment
```bash
cd bgplookingglass
sudo ./setup.sh
```

### Step 3: Create a Non-Root User and change file owners
```bash
sudo adduser -r -s /bin/false bgplookingglass
sudo usermod -s /bin/bash bgplookingglass
sudo chown bgplookingglass:bgplookingglass /opt/bgplookingglass
```

### Step 4: Test the app
```bash
source venv/bin/activate
gunicorn --workers 3 --bind 0.0.0.0:5000 --log-level debug wsgi:app
```
The app should be running at http://{{IP}}:5000

### Step 5: Configure systemd
```bash
sudo cp system_files/bgplookingglass.service /etc/systemd/system/bgplookingglass.service
sudo systemctl daemon-reload
sudo systemctl enable --now bgplookingglass
sudo systemctl status bgplookingglass
sudo systemctl restart bgplookingglass
```

### Step 6: Setup NGINX
Start and enable the service
```bash
systemctl enable --now nginx
```

Debian
```bash
sudo cp system_files/bgplookingglass.conf /etc/nginx/sites-available/bgplookingglass
```
RHEL
```bash
sudo cp system_files/bgplookingglass.conf /etc/nginx/conf.d/bgplookingglass.conf
```

Test the conig
```bash
sudo nginx -t
```

Apply the config
```bash
sudo systemctl reload nginx
```
