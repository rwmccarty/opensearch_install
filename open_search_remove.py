#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil
import argparse
from open_search_install_config import (
    OPENSEARCH_VERSION,
    OPENSEARCH_RPM_FILENAME
)

class OpenSearchRemover:
    def __init__(self, debug=False):
        self.debug = debug
        self.rpm_name = OPENSEARCH_RPM_FILENAME(OPENSEARCH_VERSION).replace(".rpm", "")
        if self.debug:
            print(f"Debug: RPM to remove: {self.rpm_name}")

    def check_root(self):
        """Check if the script is running as root"""
        if os.geteuid() != 0:
            print("❌ Error: This script must be run as root")
            print("Please run with: sudo python3 open_search_remove.py")
            sys.exit(1)
        if self.debug:
            print("✓ Running as root")

    def check_service_status(self):
        """Check if OpenSearch service is running"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "opensearch"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "active"
        except subprocess.CalledProcessError:
            return False

    def stop_service(self):
        """Stop the OpenSearch service if it's running"""
        print("\nChecking OpenSearch service status...")
        if self.check_service_status():
            print("OpenSearch service is running. Stopping service...")
            try:
                subprocess.run(["systemctl", "stop", "opensearch"], check=True)
                print("✓ OpenSearch service stopped")
            except subprocess.CalledProcessError as e:
                print("❌ Failed to stop OpenSearch service")
                if self.debug:
                    print(f"Error: {str(e)}")
                sys.exit(1)
        else:
            print("OpenSearch service is not running")

    def disable_service(self):
        """Disable the OpenSearch service"""
        print("\nDisabling OpenSearch service...")
        try:
            subprocess.run(["systemctl", "disable", "opensearch"], check=True)
            print("✓ OpenSearch service disabled")
        except subprocess.CalledProcessError as e:
            print("❌ Failed to disable OpenSearch service")
            if self.debug:
                print(f"Error: {str(e)}")

    def remove_package(self):
        """Remove OpenSearch package using yum"""
        print("\nRemoving OpenSearch package...")
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
            print("✓ OpenSearch package removed")
        except subprocess.CalledProcessError as e:
            print("❌ Failed to remove OpenSearch package")
            if self.debug:
                print(f"Error: {str(e)}")
                if e.stdout:
                    print("Stdout:", e.stdout)
                if e.stderr:
                    print("Stderr:", e.stderr)
            sys.exit(1)

    def remove_config_directory(self):
        """Remove /etc/opensearch directory"""
        config_dir = "/etc/opensearch"
        print(f"\nRemoving {config_dir} directory...")
        if os.path.exists(config_dir):
            try:
                shutil.rmtree(config_dir)
                print(f"✓ Removed {config_dir}")
            except Exception as e:
                print(f"❌ Failed to remove {config_dir}")
                if self.debug:
                    print(f"Error: {str(e)}")
                sys.exit(1)
        else:
            print(f"Directory {config_dir} does not exist")

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