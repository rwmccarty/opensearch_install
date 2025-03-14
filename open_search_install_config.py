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

OPENSEARCH_CONFIG_DIR = "/etc/opensearch"
OPENSEARCH_SERVICE_NAME = "opensearch"
OPENSEARCH_CONFIG_FILE = f"{OPENSEARCH_CONFIG_DIR}/opensearch.yml"
OPENSEARCH_JVM_FILE = f"{OPENSEARCH_CONFIG_DIR}/jvm.options"
OPENSEARCH_RPM_FILENAME = lambda version: f"opensearch-{version}-linux-x64.rpm"
OPENSEARCH_RPM_URL = lambda version: f"https://artifacts.opensearch.org/releases/bundle/opensearch/{version}/opensearch-{version}-linux-x64.rpm" 


DASHBOARD_CONFIG_DIR = "/etc/opensearch-dashboards"
DASHBOARD_SERVICE_NAME = "opensearch-dashboards"
DASHBOARD_CONFIG_FILE = f"{DASHBOARD_CONFIG_DIR}/opensearch_dashboards.yml"
DASHBOARD_RPM_FILENAME = lambda version: f"opensearch-dashboards-{version}-linux-x64.rpm"
DASHBOARD_RPM_URL = lambda version: f"https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/{version}/opensearch-dashboards-{version}-linux-x64.rpm"

    