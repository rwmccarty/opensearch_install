#!/usr/bin/env python3

import os
import subprocess
import argparse  # Importing argparse for command-line argument parsing
import platform  # For detecting OS
import sys
import time  # For sleep during startup
from open_search_install_config import ADMIN_PASSWORD, DEFAULT_VERSION, DOWNLOAD_DIR


class OpenSearchInstaller:
    def __init__(self, version, admin_password, debug=False):
        self.version = version
        self.admin_password = admin_password
        self.is_windows = platform.system().lower() == 'windows'
        self.debug = debug

    def download_opensearch(self):
        print("Downloading OpenSearch RPM...")
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
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
            
            # Construct the command with environment variable
            install_cmd = f"OPENSEARCH_INITIAL_ADMIN_PASSWORD={self.admin_password} yum localinstall {rpm_file} -y --verbose --nogpgcheck"
            
            if self.debug:
                print("\nDebug: Executing command:")
                print("----------------------------------------")
                print(install_cmd)
                print("----------------------------------------\n")
                input("Press Enter to continue...")
            
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if self.debug:
                print("\nDebug: Command completed with return code:", result.returncode)
            
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

    def verify_api(self):
        print("\nVerifying OpenSearch API...")
        try:
            result = subprocess.run(
                ["curl", "-X", "GET", "https://localhost:9200",
                 "-u", f"admin:{self.admin_password}",  # Remove the extra quotes
                 "--insecure",
                 "--silent"],
                capture_output=True,
                text=True,
                check=True
            )
            
            print("\nAPI Response:")
            print(result.stdout)
            
            if self.debug:
                print("\nDebug: Curl command:")
                print(f"curl -X GET https://localhost:9200 -u admin:{self.admin_password} --insecure --silent")
            
            try:
                import json
                response = json.loads(result.stdout)
                if response.get("tagline") == "The OpenSearch Project: https://opensearch.org/":
                    print("\n✓ OpenSearch API check passed - Service is running and responding correctly")
                    print(f"Version: {response.get('version', {}).get('number', 'unknown')}")
                    print(f"Cluster name: {response.get('cluster_name', 'unknown')}")
                    return True
                else:
                    print("\n✗ OpenSearch API check failed - Unexpected response")
                    print("Expected tagline not found in response")
                    return False
            except json.JSONDecodeError:
                print("\n✗ OpenSearch API check failed - Invalid JSON response")
                if self.debug:
                    print("Raw response received:")
                    print(repr(result.stdout))  # Print exact string representation
                return False
                
        except subprocess.CalledProcessError as e:
            print("\n✗ OpenSearch API check failed - Service not responding")
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            return False

    def verify_plugins(self):
        print("\nVerifying OpenSearch Plugins...")
        try:
            result = subprocess.run(
                ["curl", "-X", "GET", "https://localhost:9200/_cat/plugins?v",
                 "-u", f"admin:{self.admin_password}",
                 "--insecure",
                 "--silent"],
                capture_output=True,
                text=True,
                check=True
            )
            
            print("\nPlugins Response:")
            print(result.stdout if result.stdout.strip() else "No plugins installed")
            
            if self.debug:
                print("\nDebug: Curl command:")
                print(f"curl -X GET https://localhost:9200/_cat/plugins?v -u admin:{self.admin_password} --insecure --silent")
            
            return True
                
        except subprocess.CalledProcessError as e:
            print("\n✗ OpenSearch Plugins check failed - Service not responding")
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            return False

    def run_installation(self):
        if self.is_windows:
            # For Windows, we'll just download the package
            self.download_opensearch()
            print("\nFor Windows installation:")
            print("1. Extract the downloaded zip file")
            print("2. Run opensearch.bat from the extracted directory")
            print("3. Follow the OpenSearch documentation for Windows configuration")
        else:
            self.install_opensearch()
            self.enable_service()
            self.start_service()
            self.verify_service()
            # Add a small delay to allow OpenSearch to fully start
            print("\nWaiting 30 seconds for OpenSearch to fully start...")
            time.sleep(30)
            self.verify_api()
            self.verify_plugins()  # Add plugins check to full installation

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenSearch Installer")
    parser.add_argument("--download", "-d", action="store_true", help="Download OpenSearch package only, do not install or start the service.")
    parser.add_argument("--version", "-v", type=str, default=DEFAULT_VERSION, help="Specify the OpenSearch version to install.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--api", action="store_true", help="Only run the API verification test")
    parser.add_argument("--plugins", action="store_true", help="Only run the plugins endpoint test")
    
    args = parser.parse_args()
    
    installer = OpenSearchInstaller(args.version, ADMIN_PASSWORD, debug=args.debug)

    if args.api:
        installer.verify_api()  # Only run API verification
    elif args.plugins:
        installer.verify_plugins()  # Only run plugins verification
    elif args.download:
        installer.download_opensearch()  # Only download the package
    else:
        installer.run_installation()  # Proceed with installation and service management
