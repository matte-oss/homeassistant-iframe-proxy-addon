#!/usr/bin/with-contenv bashio

# Get configuration
PORT=$(bashio::config 'port')
SSL=$(bashio::config 'ssl')
CERTFILE=$(bashio::config 'certfile')
KEYFILE=$(bashio::config 'keyfile')
ALLOWED_DOMAINS=$(bashio::config 'allowed_domains')
MAX_CONTENT_SIZE=$(bashio::config 'max_content_size')
TIMEOUT=$(bashio::config 'timeout')

bashio::log.info "Starting Web Content Proxy on port ${PORT}"

# Export configuration as environment variables
export PROXY_PORT="$PORT"
export PROXY_SSL="$SSL"
export PROXY_CERTFILE="$CERTFILE"
export PROXY_KEYFILE="$KEYFILE"
export PROXY_ALLOWED_DOMAINS="$ALLOWED_DOMAINS"
export PROXY_MAX_CONTENT_SIZE="$MAX_CONTENT_SIZE"
export PROXY_TIMEOUT="$TIMEOUT"

# Start the proxy server
python3 /proxy_server.py
