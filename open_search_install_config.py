#!/usr/bin/env python3

# OpenSearch Installation Configuration

# Admin password for OpenSearch
ADMIN_PASSWORD = "asdfASDF1234-"

# OpenSearch version
OPENSEARCH_VERSION = "2.19.1"

# Feature flags
DASHBOARD = True

# Installation paths and settings
DOWNLOAD_DIR = "downloads"

# Set configuration based on DASHBOARD flag
if DASHBOARD:
    CONFIG_DIR = "/etc/opensearch-dashboards"
    SERVICE_NAME = "opensearch-dashboards"
    OPENSEARCH_RPM_FILENAME = lambda version: f"opensearch-dashboards-{version}-linux-x64.rpm"
    OPENSEARCH_RPM_URL = lambda version: f"https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/{version}/opensearch-dashboards-{version}-linux-x64.rpm"
else:
    CONFIG_DIR = "/etc/opensearch"
    SERVICE_NAME = "opensearch"
    OPENSEARCH_RPM_FILENAME = lambda version: f"opensearch-{version}-linux-x64.rpm"
    OPENSEARCH_RPM_URL = lambda version: f"https://artifacts.opensearch.org/releases/bundle/opensearch/{version}/opensearch-{version}-linux-x64.rpm" 