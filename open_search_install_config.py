#!/usr/bin/env python3

# OpenSearch Installation Configuration

# Admin password for OpenSearch
ADMIN_PASSWORD = "asdfASDF1234-"

# Default version if not specified
DEFAULT_VERSION = "2.19.1"

# Installation paths and settings
DOWNLOAD_DIR = "downloads"

# OpenSearch RPM Configuration
OPENSEARCH_RPM_FILENAME = lambda version: f"opensearch-{version}-linux-x64.rpm"
OPENSEARCH_RPM_URL = lambda version: f"https://artifacts.opensearch.org/releases/bundle/opensearch/{version}/opensearch-{version}-linux-x64.rpm"

# Dashboard Configuration
DASHBOARD_VERSION = "2.19.1"
DASHBOARD_URL = f"https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/{DASHBOARD_VERSION}/opensearch-dashboards-{DASHBOARD_VERSION}-linux-x64.rpm" 