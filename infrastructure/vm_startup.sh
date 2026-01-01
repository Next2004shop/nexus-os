#!/bin/bash
# NEXUS Core VM Startup Script
apt-get update -y
apt-get install -y python3-pip python3-venv git curl wget

# Create nexus user
useradd -m -s /bin/bash nexus

# Create directories
mkdir -p /opt/nexus
chown nexus:nexus /opt/nexus

# Log initialization
echo "NEXUS VM initialized at $(date)" > /var/log/nexus-init.log
