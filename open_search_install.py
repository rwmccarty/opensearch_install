#!/usr/bin/env python3

import os
import subprocess
import getpass  # Importing getpass for secure password input
import argparse  # Importing argparse for command-line argument parsing
import platform  # For detecting OS
import sys


class OpenSearchInstaller:
    def __init__(self, version, admin_password):
        self.version = version
        self.admin_password = admin_password
        self.is_windows = platform.system().lower() == 'windows'

    def download_opensearch(self):
        print("Downloading OpenSearch RPM...")
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        
        rpm_url = f"https://artifacts.opensearch.org/releases/bundle/opensearch/{self.version}/opensearch-{self.version}-linux-x64.rpm"
        rpm_file = os.path.join(downloads_dir, f"opensearch-{self.version}-linux-x64.rpm")
        
        # Download the RPM file
        try:
            print(f"Downloading from: {rpm_url}")
            subprocess.run(["curl", "-L", "-o", rpm_file, rpm_url], check=True)
            print(f"Downloaded OpenSearch RPM to {rpm_file}")
            
            # Verify the file exists and has size > 0
            if not os.path.exists(rpm_file) or os.path.getsize(rpm_file) == 0:
                raise Exception(f"Download failed or file is empty: {rpm_file}")
                
            # Set appropriate permissions
            subprocess.run(["sudo", "chmod", "644", rpm_file], check=True)
            return rpm_file
        except Exception as e:
            print(f"Error downloading RPM: {str(e)}")
            raise

    def install_opensearch(self):
        rpm_file = self.download_opensearch()  # Ensure the RPM is downloaded before installation
        print("Installing OpenSearch...")
        
        try:
            # First check for and install dependencies
            print("Checking and installing dependencies...")
            subprocess.run(["sudo", "yum", "install", "java-11-openjdk-devel", "-y"], check=True)
            
            # Then install the RPM with verbose output and environment variable
            print(f"Installing OpenSearch RPM from {rpm_file}...")
            env = os.environ.copy()  # Copy current environment
            env["OPENSEARCH_INITIAL_ADMIN_PASSWORD"] = self.admin_password  # Add our password
            
            result = subprocess.run(
                ["sudo", "-E", "yum", "localinstall", rpm_file, "-y", "--verbose", "--nogpgcheck"],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                print("\nInstallation failed. Full output:")
                print("\nSTDOUT:")
                print(result.stdout)
                print("\nSTDERR:")
                print(result.stderr)
                raise Exception("RPM installation failed")
            else:
                print("\nInstallation output:")
                print(result.stdout)
                
        except subprocess.CalledProcessError as e:
            print(f"\nInstallation failed: {str(e)}")
            print("\nCommand output:")
            if hasattr(e, 'stdout') and e.stdout:
                print("\nSTDOUT:")
                print(e.stdout)
            if hasattr(e, 'stderr') and e.stderr:
                print("\nSTDERR:")
                print(e.stderr)
            raise

    def enable_service(self):
        if self.is_windows:
            print("Service management not supported on Windows")
            return
            
        print("Enabling OpenSearch service...")
        try:
            subprocess.run(["sudo", "systemctl", "enable", "opensearch"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error enabling OpenSearch service: {e}")
            sys.exit(1)

    def start_service(self):
        if self.is_windows:
            print("Service management not supported on Windows")
            return
            
        print("Starting OpenSearch service...")
        try:
            subprocess.run(["sudo", "systemctl", "start", "opensearch"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error starting OpenSearch service: {e}")
            sys.exit(1)

    def verify_service(self):
        if self.is_windows:
            print("Service verification not supported on Windows")
            return
            
        print("Verifying OpenSearch service status...")
        try:
            subprocess.run(["sudo", "systemctl", "status", "opensearch"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error verifying OpenSearch service: {e}")
            sys.exit(1)

    def run_installation(self):
        if self.is_windows:
            # For Windows, we'll just download the package
            self.download_opensearch()
            print("\nFor Windows installation:")
            print("1. Extract the downloaded zip file")
            print("2. Run opensearch.bat from the extracted directory")
            print("3. Follow the OpenSearch documentation for Windows configuration")
        else:
            # Set password in environment before installation
            os.environ["OPENSEARCH_INITIAL_ADMIN_PASSWORD"] = self.admin_password
            self.install_opensearch()
            self.enable_service()
            self.start_service()
            self.verify_service()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenSearch Installer")
    parser.add_argument("--download", "-d", action="store_true", help="Download OpenSearch package only, do not install or start the service.")
    parser.add_argument("--version", "-v", type=str, default="2.19.1", help="Specify the OpenSearch version to install.")
    
    args = parser.parse_args()
    
    # Only prompt for password if we're doing a full installation
    admin_password = None
    if not args.download:
        admin_password = getpass.getpass("Enter the OpenSearch admin password: ")  # Prompt for password
    
    installer = OpenSearchInstaller(args.version, admin_password)

    if args.download:
        installer.download_opensearch()  # Only download the package
    else:
        installer.run_installation()  # Proceed with installation and service management
