#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil
import argparse
from open_search_install_config import (
    OPENSEARCH_VERSION,
    OPENSEARCH_RPM_FILENAME,
    DASHBOARD_RPM_FILENAME,
    OPENSEARCH_CONFIG_DIR,
    DASHBOARD_CONFIG_DIR,
    OPENSEARCH_SERVICE_NAME,
    DASHBOARD_SERVICE_NAME
)

class OpenSearchRemover:
    def __init__(self, debug=False):
        self.debug = debug
        self.opensearch_rpm = OPENSEARCH_RPM_FILENAME(OPENSEARCH_VERSION).replace(".rpm", "")
        self.dashboard_rpm = DASHBOARD_RPM_FILENAME(OPENSEARCH_VERSION).replace(".rpm", "")
        if self.debug:
            print(f"Debug: OpenSearch RPM to remove: {self.opensearch_rpm}")
            print(f"Debug: Dashboard RPM to remove: {self.dashboard_rpm}")
            print(f"Debug: OpenSearch config directory to remove: {OPENSEARCH_CONFIG_DIR}")
            print(f"Debug: Dashboard config directory to remove: {DASHBOARD_CONFIG_DIR}")
            print(f"Debug: OpenSearch service name: {OPENSEARCH_SERVICE_NAME}")
            print(f"Debug: Dashboard service name: {DASHBOARD_SERVICE_NAME}")

    def check_root(self):
        """Check if the script is running as root"""
        if os.geteuid() != 0:
            print("❌ Error: This script must be run as root")
            print("Please run with: sudo python3 open_search_remove.py")
            sys.exit(1)
        if self.debug:
            print("✓ Running as root")

    def check_service_status(self, service_name):
        """Check if service is running"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "active"
        except subprocess.CalledProcessError:
            return False

    def stop_service(self, service_name):
        """Stop the service if it's running"""
        print(f"\nChecking {service_name} service status...")
        if self.check_service_status(service_name):
            print(f"{service_name} service is running. Stopping service...")
            try:
                subprocess.run(["systemctl", "stop", service_name], check=True)
                print(f"✓ {service_name} service stopped")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to stop {service_name} service")
                if self.debug:
                    print(f"Error: {str(e)}")
                sys.exit(1)
        else:
            print(f"{service_name} service is not running")

    def disable_service(self, service_name):
        """Disable the service"""
        print(f"\nDisabling {service_name} service...")
        try:
            subprocess.run(["systemctl", "disable", service_name], check=True)
            print(f"✓ {service_name} service disabled")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to disable {service_name} service")
            if self.debug:
                print(f"Error: {str(e)}")

    def remove_package(self, rpm_name, service_name):
        """Remove package using yum"""
        print(f"\nRemoving {service_name} package...")
        try:
            result = subprocess.run(
                ["yum", "remove", rpm_name, "-y"],
                capture_output=True,
                text=True,
                check=True
            )
            if self.debug:
                print("\nYum remove output:")
                print(result.stdout)
            print(f"✓ {service_name} package removed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to remove {service_name} package")
            if self.debug:
                print(f"Error: {str(e)}")
                if e.stdout:
                    print("Stdout:", e.stdout)
                if e.stderr:
                    print("Stderr:", e.stderr)
            sys.exit(1)

    def remove_config_directory(self, config_dir, service_name):
        """Remove configuration directory"""
        print(f"\nRemoving {config_dir} directory...")
        if os.path.exists(config_dir):
            try:
                shutil.rmtree(config_dir)
                print(f"✓ Removed {service_name} config directory")
            except Exception as e:
                print(f"❌ Failed to remove {config_dir}")
                if self.debug:
                    print(f"Error: {str(e)}")
                sys.exit(1)
        else:
            print(f"Directory {config_dir} does not exist")

    def run_removal(self):
        """Run the complete removal process"""
        print("Starting OpenSearch and Dashboard removal process...")
        self.check_root()

        # Remove Dashboard first
        print("\nRemoving OpenSearch Dashboard...")
        self.stop_service(DASHBOARD_SERVICE_NAME)
        self.disable_service(DASHBOARD_SERVICE_NAME)
        self.remove_package(self.dashboard_rpm, DASHBOARD_SERVICE_NAME)
        self.remove_config_directory(DASHBOARD_CONFIG_DIR, DASHBOARD_SERVICE_NAME)

        # Then remove OpenSearch
        print("\nRemoving OpenSearch...")
        self.stop_service(OPENSEARCH_SERVICE_NAME)
        self.disable_service(OPENSEARCH_SERVICE_NAME)
        self.remove_package(self.opensearch_rpm, OPENSEARCH_SERVICE_NAME)
        self.remove_config_directory(OPENSEARCH_CONFIG_DIR, OPENSEARCH_SERVICE_NAME)

        print("\n✓ OpenSearch and Dashboard removal completed successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenSearch and Dashboard Removal Script")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    remover = OpenSearchRemover(debug=args.debug)
    remover.run_removal() 