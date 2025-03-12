#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil
import argparse
from open_search_install_config import (
    OPENSEARCH_VERSION,
    OPENSEARCH_RPM_FILENAME,
    CONFIG_DIR,
    SERVICE_NAME
)

class OpenSearchRemover:
    def __init__(self, debug=False):
        self.debug = debug
        self.rpm_name = OPENSEARCH_RPM_FILENAME(OPENSEARCH_VERSION).replace(".rpm", "")
        if self.debug:
            print(f"Debug: RPM to remove: {self.rpm_name}")
            print(f"Debug: Config directory to remove: {CONFIG_DIR}")
            print(f"Debug: Service name to manage: {SERVICE_NAME}")

    def check_root(self):
        """Check if the script is running as root"""
        if os.geteuid() != 0:
            print("❌ Error: This script must be run as root")
            print("Please run with: sudo python3 open_search_remove.py")
            sys.exit(1)
        if self.debug:
            print("✓ Running as root")

    def check_service_status(self):
        """Check if service is running"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", SERVICE_NAME],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "active"
        except subprocess.CalledProcessError:
            return False

    def stop_service(self):
        """Stop the service if it's running"""
        print(f"\nChecking {SERVICE_NAME} service status...")
        if self.check_service_status():
            print(f"{SERVICE_NAME} service is running. Stopping service...")
            try:
                subprocess.run(["systemctl", "stop", SERVICE_NAME], check=True)
                print(f"✓ {SERVICE_NAME} service stopped")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to stop {SERVICE_NAME} service")
                if self.debug:
                    print(f"Error: {str(e)}")
                sys.exit(1)
        else:
            print(f"{SERVICE_NAME} service is not running")

    def disable_service(self):
        """Disable the service"""
        print(f"\nDisabling {SERVICE_NAME} service...")
        try:
            subprocess.run(["systemctl", "disable", SERVICE_NAME], check=True)
            print(f"✓ {SERVICE_NAME} service disabled")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to disable {SERVICE_NAME} service")
            if self.debug:
                print(f"Error: {str(e)}")

    def remove_package(self):
        """Remove package using yum"""
        print(f"\nRemoving {SERVICE_NAME} package...")
        try:
            result = subprocess.run(
                ["yum", "remove", self.rpm_name, "-y"],
                capture_output=True,
                text=True,
                check=True
            )
            if self.debug:
                print("\nYum remove output:")
                print(result.stdout)
            print(f"✓ {SERVICE_NAME} package removed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to remove {SERVICE_NAME} package")
            if self.debug:
                print(f"Error: {str(e)}")
                if e.stdout:
                    print("Stdout:", e.stdout)
                if e.stderr:
                    print("Stderr:", e.stderr)
            sys.exit(1)

    def remove_config_directory(self):
        """Remove configuration directory"""
        print(f"\nRemoving {CONFIG_DIR} directory...")
        if os.path.exists(CONFIG_DIR):
            try:
                shutil.rmtree(CONFIG_DIR)
                print(f"✓ Removed {CONFIG_DIR}")
            except Exception as e:
                print(f"❌ Failed to remove {CONFIG_DIR}")
                if self.debug:
                    print(f"Error: {str(e)}")
                sys.exit(1)
        else:
            print(f"Directory {CONFIG_DIR} does not exist")

    def run_removal(self):
        """Run the complete removal process"""
        print("Starting OpenSearch removal process...")
        self.check_root()
        self.stop_service()
        self.disable_service()
        self.remove_package()
        self.remove_config_directory()
        print("\n✓ OpenSearch removal completed successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenSearch Removal Script")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    remover = OpenSearchRemover(debug=args.debug)
    remover.run_removal() 