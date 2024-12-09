#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

def run_command(cmd, check=True):
    try:
        subprocess.run(cmd, check=check, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def setup_java(java_path):
    # Create symbolic link for Java
    if os.path.exists('/glide/java'):
        os.remove('/glide/java')
    os.symlink(java_path, '/glide/java')
    
    # Verify Java installation
    run_command('/glide/java/bin/java -version')

def deploy_instance(node_name, port, orbit_package):
    # Deploy ServiceNow instance
    deploy_cmd = f"/glide/java/bin/java -jar {orbit_package} --dst-dir /glide/nodes/{node_name}_{port} install -n {node_name} -p {port}"
    run_command(deploy_cmd)
    
    # Set ownership
    run_command(f"chown -R servicenow:servicenow /glide/nodes/{node_name}_{port}")

def configure_node(node_name, port, db_host, db_user, db_pass):
    node_dir = f"/glide/nodes/{node_name}_{port}"
    
    # Configure glide.properties
    with open(f"{node_dir}/conf/glide.properties", 'a') as f:
        f.write(f"\nglide.proxy.host = https://example.service-now.com")
        f.write(f"\nglide.proxy.path = /")
        f.write(f"\nglide.servlet.port = {port}")
        f.write(f"\nglide.cluster.node_name = {node_name}")
    
    # Configure database properties
    with open(f"{node_dir}/conf/glide.db.properties", 'w') as f:
        f.write(f"glide.db.name = {node_name}_{port}\n")
        f.write("glide.db.rdbms = mysql\n")
        f.write(f"glide.db.url = jdbc:mysql://{db_host}:3306/\n")
        f.write(f"glide.db.user = {db_user}\n")
        f.write(f"glide.db.password = {db_pass}\n")

def setup_systemd(node_name, port):
    service_content = f"""[Unit]
Description=ServiceNow Tomcat Container
After=syslog.target

[Service]
Type=forking
ExecStart=/glide/nodes/{node_name}_{port}/startup.sh
ExecStop=/glide/nodes/{node_name}_{port}/shutdown.sh
User=servicenow
Group=servicenow
UMask=0007
LimitNOFILE=16000

[Install]
WantedBy=multi-user.target"""
    
    service_file = f"/etc/systemd/system/snc_{node_name}.service"
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    run_command("systemctl daemon-reload")
    run_command(f"systemctl enable snc_{node_name}.service")

def main():
    parser = argparse.ArgumentParser(description='Deploy ServiceNow instance')
    parser.add_argument('--java-path', required=True, help='Path to Java installation')
    parser.add_argument('--node-name', required=True, help='Node name')
    parser.add_argument('--port', required=True, type=int, help='Port number')
    parser.add_argument('--orbit-package', required=True, help='Path to orbit package')
    parser.add_argument('--db-host', required=True, help='Database host')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-pass', required=True, help='Database password')
    
    args = parser.parse_args()
    
    # Execute deployment steps
    setup_java(args.java_path)
    deploy_instance(args.node_name, args.port, args.orbit_package)
    configure_node(args.node_name, args.port, args.db_host, args.db_user, args.db_pass)
    setup_systemd(args.node_name, args.port)
    
    print(f"ServiceNow instance {args.node_name} deployed successfully")

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("This script must be run as root")
        sys.exit(1)
    main()
