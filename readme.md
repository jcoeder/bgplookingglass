# BGP Looking Glass

A Flask-based web application for executing network commands on configured devices and retrieving raw output in JSON format. This tool provides a user-friendly interface and API for BGP and network diagnostics.

Repository: [https://github.com/jcoeder/bgplookingglass](https://github.com/jcoeder/bgplookingglass)

## Prerequisites

- A Linux-based system (RHEL 8/9 or Ubuntu 20.04/22.04 or later)
- Python 3.8 or higher
- Git
- Nginx
- Access to a user with sudo privileges for initial setup

## Setup Instructions

This guide will walk you through setting up the BGP Looking Glass app as a non-root user named `bgplookingglass`, installing it in `/opt/bgplookingglass`, and configuring it to run as a systemd service with Nginx as a reverse proxy. Instructions are provided for both RHEL and Ubuntu systems.

### Step 1: Create a Non-Root User

Log in as a user with sudo privileges and create a new system user named `bgplookingglass`:

```bash
sudo adduser --system --group --home /home/bgplookingglass bgplookingglass
sudo usermod -s /bin/bash bgplookingglass
```
