#!/usr/bin/env python3

import os
import subprocess
import argparse  # Importing argparse for command-line argument parsing
import platform  # For detecting OS
import sys
import time  # For sleep during startup
from open_search_install_config import (
    ADMIN_PASSWORD, 
    OPENSEARCH_VERSION, 
    DOWNLOAD_DIR,
    OPENSEARCH_RPM_URL,
    OPENSEARCH_RPM_FILENAME,
    CONFIG_DIR,
    CONFIG_FILE,
    JVM_FILE,
    SERVICE_NAME,
    DASHBOARD
)

class OpenSearchInstaller:
    def __init__(self, version, admin_password, debug=False):
        self.version = version
        self.admin_password = admin_password
        self.debug = debug

    def download_opensearch(self):
        print(f"Downloading {SERVICE_NAME} RPM...")
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
        os.makedirs(downloads_dir, exist_ok=True)
        
        opensearch_rpm_url = OPENSEARCH_RPM_URL(self.version)
        opensearch_rpm_file = os.path.join(downloads_dir, OPENSEARCH_RPM_FILENAME(self.version))
        
        # Download the RPM file
        try:
            print(f"Downloading from: {opensearch_rpm_url}")
            print(f"Downloading to: {downloads_dir}")
            subprocess.run(["curl", "-L", "-o", opensearch_rpm_file, opensearch_rpm_url], check=True)
            print(f"Downloaded {SERVICE_NAME} RPM to {opensearch_rpm_file}")
            
            # Verify the file exists and has size > 0
            if not os.path.exists(opensearch_rpm_file) or os.path.getsize(opensearch_rpm_file) == 0:
                raise Exception(f"Download failed or file is empty: {opensearch_rpm_file}")
                
            # Set appropriate permissions
            subprocess.run(["sudo", "chmod", "644", opensearch_rpm_file], check=True)
            return opensearch_rpm_file
        except Exception as e:
            print(f"Error downloading RPM: {str(e)}")
            raise

    def install_deps(self):
        print("\nChecking and installing dependencies...")
        start_time = time.time()
        try:
            subprocess.run(["yum", "install", "java-11-openjdk-devel", "-y"], 
                         check=True,
                         text=True,
                         stdout=sys.stdout,
                         stderr=sys.stderr)
            print(f"Dependencies installation took {time.time() - start_time:.1f} seconds")
        except subprocess.CalledProcessError as e:
            print(f"\nDependency installation failed with return code {e.returncode}")
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            raise Exception(f"Dependency installation failed: {str(e)}")

    def opensearch_install(self):
        rpm_file = self.download_opensearch()  # Ensure the RPM is downloaded before installation
        print(f"Installing {SERVICE_NAME}...")
        
        try:
            # Install dependencies first
            self.install_deps()
            
            # Then install the RPM with verbose output
            print(f"\nInstalling {SERVICE_NAME} RPM from {rpm_file}...")
            
            # Prepare the installation command with password in the command string
            install_cmd = f"OPENSEARCH_INITIAL_ADMIN_PASSWORD={self.admin_password} yum localinstall {rpm_file} -y --verbose --nogpgcheck"
            
            if self.debug:
                print("\nDebug: Executing command:")
                print("----------------------------------------")
                print(install_cmd)
                print("----------------------------------------\n")
                input("Press Enter to continue...")
            
            # Run the installation with real-time output
            print("\nInstalling RPM (this may take a few minutes)...")
            start_time = time.time()
            
            # Use Popen to get more control over the process
            process = subprocess.Popen(
                install_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Poll process while printing output in real-time
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                error = process.stderr.readline()
                if error:
                    print(error.strip(), file=sys.stderr)
                
                # Check if process has finished
                return_code = process.poll()
                if return_code is not None:
                    # Process has completed
                    # Print any remaining output
                    for output in process.stdout.readlines():
                        if output:
                            print(output.strip())
                    for error in process.stderr.readlines():
                        if error:
                            print(error.strip(), file=sys.stderr)
                    
                    if return_code != 0:
                        raise subprocess.CalledProcessError(return_code, install_cmd)
                    break

            elapsed_time = time.time() - start_time
            print(f"\nInstallation process took {elapsed_time:.1f} seconds")
            
            # Add a small delay to ensure package database is updated
            time.sleep(2)
            
            # Verify RPM installation
            print("\nVerifying RPM installation...")
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                verify_result = subprocess.run(f"rpm -q {SERVICE_NAME}",
                                            shell=True,
                                            text=True,
                                            capture_output=True)
                
                if verify_result.returncode == 0:
                    print(f"\n✓ {SERVICE_NAME} RPM installed successfully")
                    if self.debug:
                        print("Installed package:", verify_result.stdout.strip())
                    break
                else:
                    if attempt < max_retries - 1:
                        print(f"Verification attempt {attempt + 1} failed, waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print("\nInstallation verification failed")
                        raise Exception("RPM installation verification failed")
                
        except subprocess.CalledProcessError as e:
            print(f"\nInstallation failed with return code {e.returncode}")
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            raise Exception(f"Installation failed: {str(e)}")
        except Exception as e:
            print(f"\nInstallation failed: {str(e)}")
            raise

    def service_enable(self):
        print(f"Enabling {SERVICE_NAME} service...")
        try:
            subprocess.run(["sudo", "systemctl", "enable", SERVICE_NAME], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error enabling {SERVICE_NAME} service: {e}")
            sys.exit(1)

    def service_start(self):
        print(f"Starting {SERVICE_NAME} service...")
        try:
            subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error starting {SERVICE_NAME} service: {e}")
            sys.exit(1)

    def service_verify(self):
        print(f"Verifying {SERVICE_NAME} service status...")
        try:
            subprocess.run(["sudo", "systemctl", "status", SERVICE_NAME], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error verifying {SERVICE_NAME} service: {e}")
            sys.exit(1)

    def service_wrapper(self):
        """Wrapper function to enable and start the service, then wait for startup"""
        self.service_enable()
        self.service_start()
        print(f"\nWaiting 30 seconds for {SERVICE_NAME} to fully start...")
        time.sleep(30)
        self.service_verify()

    def configuration_wrapper(self):
        """Wrapper function to handle all configuration and verification steps"""
        self.opensearch_config_update()
        if not DASHBOARD:
            self.set_jvm_heap()
        self.api_verify()
        self.plugins_verify()

    def api_verify(self):
        print(f"\nVerifying {SERVICE_NAME} API...")
        try:
            result = subprocess.run(
                ["curl", "-X", "GET", "https://localhost:9200",
                 "-u", f"admin:{self.admin_password}",
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
                    print(f"\n✓ {SERVICE_NAME} API check passed - Service is running and responding correctly")
                    print(f"Version: {response.get('version', {}).get('number', 'unknown')}")
                    print(f"Cluster name: {response.get('cluster_name', 'unknown')}")
                    return True
                else:
                    print(f"\n✗ {SERVICE_NAME} API check failed - Unexpected response")
                    print("Expected tagline not found in response")
                    return False
            except json.JSONDecodeError:
                print(f"\n✗ {SERVICE_NAME} API check failed - Invalid JSON response")
                if self.debug:
                    print("Raw response received:")
                    print(repr(result.stdout))
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"\n✗ {SERVICE_NAME} API check failed - Service not responding")
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            return False

    def plugins_verify(self):
        print(f"\nVerifying {SERVICE_NAME} Plugins...")
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
            print(f"\n✗ {SERVICE_NAME} Plugins check failed - Service not responding")
            if e.stderr:
                print("Error output:")
                print(e.stderr)
            return False

    def provision_dashboard(self):
        """Provision the Dashboard service"""
        print(f"\nProvisioning {SERVICE_NAME}...")
        try:
            # Enable the dashboard service
            print(f"Enabling {SERVICE_NAME} service...")
            subprocess.run(["sudo", "systemctl", "enable", SERVICE_NAME], check=True)
            
            # Start the dashboard service
            print(f"Starting {SERVICE_NAME} service...")
            subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME], check=True)
            
            # Verify the dashboard service status
            print(f"Verifying {SERVICE_NAME} service status...")
            subprocess.run(["sudo", "systemctl", "status", SERVICE_NAME], check=True)
            
            print(f"✓ {SERVICE_NAME} service provisioned successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ Error provisioning {SERVICE_NAME} service: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                print("Error output:")
                print(e.stderr)
            return False

    def verify_config(self):
        print(f"\nVerifying {SERVICE_NAME} configuration...")
        required_settings = {
            'network.host': '0.0.0.0',
            'discovery.type': 'single-node',
            'plugins.security.disabled': 'false'
        }
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_content = f.read()
            
            # Parse the YAML content line by line to handle comments
            lines = config_content.split('\n')
            found_settings = {}
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        if key in required_settings:
                            found_settings[key] = value
            
            # Check if all required settings are present and correct
            all_correct = True
            for key, expected_value in required_settings.items():
                if key not in found_settings:
                    print(f"✗ Missing setting: {key}")
                    all_correct = False
                elif found_settings[key] != expected_value:
                    print(f"✗ Incorrect value for {key}. Expected: {expected_value}, Found: {found_settings[key]}")
                    all_correct = False
                elif self.debug:
                    print(f"✓ Verified {key}: {found_settings[key]}")
            
            if all_correct:
                print("✓ All configuration settings are correct")
                return True
            else:
                print("✗ Some configuration settings are missing or incorrect")
                return False
                
        except Exception as e:
            print(f"✗ Error verifying configuration: {str(e)}")
            return False

    def opensearch_config_update(self):
        print("\nUpdating configuration...")
        
        # Configuration to add
        new_config = """
# Bind to the correct network interface. Use 0.0.0.0
# to include all available interfaces or specify an IP address
# assigned to a specific interface.
network.host: 0.0.0.0

# Unless you have already configured a cluster, you should set
# discovery.type to single-node, or the bootstrap checks will
# fail when you try to start the service.
discovery.type: single-node

# If you previously disabled the Security plugin in opensearch.yml,
# be sure to re-enable it. Otherwise you can skip this setting.
plugins.security.disabled: false
"""
        try:
            # Read existing config
            with open(CONFIG_FILE, 'r') as f:
                existing_config = f.read()

            # Remove any existing settings we're about to add
            lines = existing_config.split('\n')
            filtered_lines = []
            skip_next = False
            
            for line in lines:
                if skip_next:
                    skip_next = False
                    continue
                    
                # Skip comments before our settings and the settings themselves
                if any(setting in line for setting in ['network.host:', 'discovery.type:', 'plugins.security.disabled:']):
                    skip_next = True  # Skip the next line if it's a value
                    continue
                if line.strip().startswith('#') and any(text in line for text in ['network.host', 'discovery.type', 'plugins.security.disabled']):
                    continue
                    
                filtered_lines.append(line)

            # Combine filtered config with new settings
            updated_config = '\n'.join(filtered_lines).strip() + new_config

            # Write updated config
            with open(CONFIG_FILE, 'w') as f:
                f.write(updated_config)

            print("✓ Configuration updated successfully")
            
            if self.debug:
                print("\nDebug: Updated configuration:")
                print(updated_config)
            
            # Verify the configuration after update
            self.verify_config()
                
        except Exception as e:
            print(f"✗ Error updating configuration: {str(e)}")
            raise

    def set_jvm_heap(self):
        print("\nUpdating JVM heap settings...")
        
        try:
            # Read existing JVM options
            with open(JVM_FILE, 'r') as f:
                lines = f.readlines()
            
            # Remove existing Xms and Xmx settings
            new_lines = []
            for line in lines:
                if not line.strip().startswith('-Xms') and not line.strip().startswith('-Xmx'):
                    new_lines.append(line)
            
            # Add our heap settings
            new_lines.append('-Xms8g\n')
            new_lines.append('-Xmx8g\n')
            
            # Write updated config
            with open(JVM_FILE, 'w') as f:
                f.writelines(new_lines)
            
            print("✓ JVM heap settings updated successfully")
            
            if self.debug:
                print("\nDebug: Updated JVM settings:")
                print(''.join(new_lines))
            
            # Verify the settings after update
            self.check_jvm_heap()
                
        except Exception as e:
            print(f"✗ Error updating JVM heap settings: {str(e)}")
            raise

    def check_jvm_heap(self):
        print("\nVerifying JVM heap settings...")
        required_settings = {
            '-Xms': '8g',
            '-Xmx': '8g'
        }
        
        try:
            with open(JVM_FILE, 'r') as f:
                lines = f.readlines()
            
            found_settings = {}
            for line in lines:
                line = line.strip()
                if line.startswith('-Xms'):
                    found_settings['-Xms'] = line[4:]
                elif line.startswith('-Xmx'):
                    found_settings['-Xmx'] = line[4:]
            
            # Check if all required settings are present and correct
            all_correct = True
            for key, expected_value in required_settings.items():
                if key not in found_settings:
                    print(f"✗ Missing setting: {key}")
                    all_correct = False
                elif found_settings[key] != expected_value:
                    print(f"✗ Incorrect value for {key}. Expected: {expected_value}, Found: {found_settings[key]}")
                    all_correct = False
                elif self.debug:
                    print(f"✓ Verified {key}: {found_settings[key]}")
            
            if all_correct:
                print("✓ All JVM heap settings are correct")
                return True
            else:
                print("✗ Some JVM heap settings are missing or incorrect")
                return False
                
        except Exception as e:
            print(f"✗ Error verifying JVM heap settings: {str(e)}")
            return False

    def run_installation(self):
        self.opensearch_install()
        self.service_wrapper()
        self.configuration_wrapper()
        if DASHBOARD:
            self.provision_dashboard()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{SERVICE_NAME} Installer")
    parser.add_argument("--download", "-d", action="store_true", help=f"Download {SERVICE_NAME} package only, do not install or start the service.")
    parser.add_argument("--version", "-v", type=str, default=OPENSEARCH_VERSION, help=f"Specify the {SERVICE_NAME} version to install.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--api", action="store_true", help="Only run the API verification test")
    parser.add_argument("--plugins", action="store_true", help="Only run the plugins endpoint test")
    parser.add_argument("--checkconfig", action="store_true", help=f"Verify {SERVICE_NAME} configuration settings")
    parser.add_argument("--checkjvm", action="store_true", help="Verify JVM heap settings")
    
    args = parser.parse_args()
    
    installer = OpenSearchInstaller(args.version, ADMIN_PASSWORD, debug=args.debug)

    if args.api:
        installer.api_verify()  # Only run API verification
    elif args.plugins:
        installer.plugins_verify()  # Only run plugins verification
    elif args.checkconfig:
        installer.verify_config()  # Only verify configuration
    elif args.checkjvm:
        installer.check_jvm_heap()  # Only verify JVM settings
    elif args.download:
        print("Downloading OpenSearch package...")
        installer.download_opensearch()  # Download OpenSearch package
    else:
        installer.run_installation()  # Proceed with installation and service management
