#!/usr/bin/env python3

import os
import subprocess
import getpass  # Importing getpass for secure password input
import argparse  # Importing argparse for command-line argument parsing

class OpenSearchInstaller:
    def __init__(self, version, admin_password):
        self.version = version
        self.admin_password = admin_password
    def download_opensearch(self):
        print("Downloading OpenSearch RPM...")
        rpm_url = f"https://artifacts.opensearch.org/releases/bundle/opensearch/{self.version}/rpm/opensearch-{self.version}-1.x86_64.rpm"
        rpm_file = f"/tmp/opensearch-{self.version}-1.x86_64.rpm"
        
        # Download the RPM file
        subprocess.run(["curl", "-L", "-o", rpm_file, rpm_url], check=True)
        print(f"Downloaded OpenSearch RPM to {rpm_file}")

    def install_opensearch(self):
        self.download_opensearch()  # Ensure the RPM is downloaded before installation
        print("Installing OpenSearch...")
        rpm_file = f"/tmp/opensearch-{self.version}-1.x86_64.rpm"
        subprocess.run(["sudo", "yum", "localinstall", rpm_file, "-y"], check=True)

    def enable_service(self):
        print("Enabling OpenSearch service...")
        subprocess.run(["sudo", "systemctl", "enable", "opensearch"], check=True)

    def start_service(self):
        print("Starting OpenSearch service...")
        subprocess.run(["sudo", "systemctl", "start", "opensearch"], check=True)

    def verify_service(self):
        print("Verifying OpenSearch service status...")
        subprocess.run(["sudo", "systemctl", "status", "opensearch"], check=True)

    def run_installation(self):
        self.install_opensearch()
        self.enable_service()
        self.start_service()
        self.verify_service()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenSearch Installer")
    parser.add_argument("--download", "-d", action="store_true", help="Download OpenSearch RPM only, do not install or start the service.")
    parser.add_argument("--version", "-v", type=str, default="2.19.1", help="Specify the OpenSearch version to install.")
    
    args = parser.parse_args()
    
    admin_password = getpass.getpass("Enter the OpenSearch admin password: ")  # Prompt for password
    installer = OpenSearchInstaller(args.version, admin_password)

    if args.download:
        installer.download_opensearch()  # Only download the RPM
    else:
        installer.run_installation()  # Proceed with installation and service management
