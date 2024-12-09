#!/bin/bash

# Initial setup script for ServiceNow deployment on EC2
# This script handles basic system configuration based on ServiceNow requirements

# Exit on any error
set -e

echo "Starting ServiceNow initial setup..."

# Create servicenow user
useradd servicenow

# Install required packages
echo "Installing required packages..."
dnf install -y \
    glibc \
    libgcc \
    rng-tools \
    fontconfig \
    libaio \
    perl

# Start and enable rngd service for Rome and later releases
systemctl start rngd
systemctl enable rngd

# Configure system settings
echo "Configuring system settings..."

# Set swappiness
echo "vm.swappiness=1" >> /etc/sysctl.conf
sysctl -p

# Configure process and file limits
cat > /etc/security/limits.d/90-nproc.conf << EOF
* soft nproc 10240
EOF

cat > /etc/security/limits.d/amb-sockets.conf << EOF
* soft nofile 16000
* hard nofile 16000
EOF

# Set locale to UTF-8
localectl set-locale LANG=en_US.UTF-8

# Create required directories
echo "Creating ServiceNow directories..."
mkdir -p /glide/nodes
chown -R servicenow:servicenow /glide

# Disable SELinux (not recommended in enforcing mode for ServiceNow)
sed -i 's/SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config
setenforce 0

# Set timezone to UTC
timedatectl set-timezone UTC

echo "Initial setup complete. Please proceed with JDK installation and ServiceNow application deployment."