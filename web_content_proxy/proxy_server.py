#!/usr/bin/env python3
"""
Home Assistant Web Content Proxy Addon
Replicates PHP proxy functionality for bypassing CORS and X-Frame-Options restrictions
"""

import os
import re
import json
import logging
import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, quote
from flask import Flask, request, Response, render_template_string
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
PORT = int(os.getenv('PROXY_PORT', 8099))
SSL_ENABLED = os.getenv('PROXY_SSL', 'false').lower() == 'true'
CERT_FILE = os.getenv('PROXY_CERTFILE', '')
KEY_FILE = os.getenv('PROXY_KEYFILE', '')
ALLOWED_DOMAINS = json.loads(os.getenv('PROXY_ALLOWED_DOMAINS', '[]'))
MAX_CONTENT_SIZE = int(os.getenv('PROXY_MAX_CONTENT_SIZE', 10485760))
TIMEOUT = int(os.getenv('PROXY_TIMEOUT', 30))

# HTML template for the main interface
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Content Proxy</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        input[type="url"] { width: 70%; padding: 10px; margin: 10px 0; }
        button { padding: 10px 20px; background: #0066cc; color: white; border: none; cursor: pointer; }
        button:hover { background: #0052a3; }
        .error { color: red; margin: 10px 0; }
        .info { color: #666; margin: 10px 0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Content Proxy</h1>
        <p>Enter a URL to proxy through this service:</p>
        
        <form id="proxyForm">
            <input type="url" id="urlInput" placeholder="https://example.com" required>
            <button type="submit">Load</button>
        </form>
        
        <div class="info">
            <p><strong>Note:</strong> This proxy bypasses CORS restrictions and X-Frame-Options headers.</p>
            {% if allowed_domains %}
            <p><strong>Allowed domains:</strong> {{ allowed_domains|join(', ') }}</p>
            {% endif %}
        </div>
        
        <div id="error" class="error"></div>
    </div>

    <script>
        document.getElementById('proxyForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const url = document.getElementById('urlInput').value;
            if (url) {
                window.location.href = '/proxy?url=' + encodeURIComponent(url);
            }
        });
    </script>
</body>
</html>
"""

def is_domain_allowed(url):
    """Check if the domain is in the allowed list (if configured)"""
    if not ALLOWED_DOMAINS:
        return True
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    for allowed in ALLOWED_DOMAINS:
        if domain == allowed.lower() or domain.endswith('.' + allowed.lower()):
            return True
    
    return False

def fetch_content(url):
    """Fetch content from URL using requests"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(
            url, 
            headers=headers, 
            timeout=TIMEOUT,
            allow_redirects=True,
            stream=True
        )
        
        # Check content size
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > MAX_CONTENT_SIZE:
            return None, f"Content too large ({content_length} bytes)"
        
        # Read content with size limit
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_CONTENT_SIZE:
                return None, f"Content exceeds maximum size ({MAX_CONTENT_SIZE} bytes)"
        
        return response, content.decode('utf-8', errors='ignore')
    
    except requests.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None, str(e)

def rewrite_urls(content, base_url, current_url):
    """Rewrite URLs in HTML content to proxy through this service"""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Attributes that contain URLs
        url_attrs = {
            'a': 'href',
            'img': 'src',
            'script': 'src',
            'link': 'href',
            'iframe': 'src',
            'form': 'action',
            'audio': 'src',
            'video': 'src',
            'source': 'src',
            'track': 'src'
        }
        
        for tag_name, attr_name in url_attrs.items():
            for tag in soup.find_all(tag_name):
                if tag.get(attr_name):
                    original_url = tag[attr_name]
                    
                    # Skip data URLs, javascript URLs, and anchors
                    if (original_url.startswith(('data:', 'javascript:', 'mailto:', '#')) or 
                        original_url.startswith('//')):
                        continue
                    
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(current_url, original_url)
                    
                    # Proxy the URL
                    proxied_url = f'/proxy?url={quote(absolute_url)}'
                    tag[attr_name] = proxied_url
        
        # Handle CSS url() references
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                style_content = style_tag.string
                style_content = re.sub(
                    r'url\([\'"]?([^\'")]+)[\'"]?\)',
                    lambda m: f'url("/proxy?url={quote(urljoin(current_url, m.group(1)))}")',
                    style_content
                )
                style_tag.string = style_content
        
        return str(soup)
    
    except Exception as e:
        logger.error(f"Error rewriting URLs: {e}")
        return content

def rewrite_js_content(content, base_url):
    """Rewrite JavaScript content to handle dynamic URL creation"""
    # Basic JavaScript URL rewriting
    patterns = [
        (r'window\.location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', 
         r'window.location.href="/proxy?url=" + encodeURIComponent("\1")'),
        (r'location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', 
         r'location.href="/proxy?url=" + encodeURIComponent("\1")'),
        (r'document\.URL\s*=\s*[\'"]([^\'"]+)[\'"]', 
         r'document.URL="/proxy?url=" + encodeURIComponent("\1")')
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    return content

@app.route('/')
def index():
    """Main interface for the proxy"""
    return render_template_string(MAIN_TEMPLATE, allowed_domains=ALLOWED_DOMAINS)

@app.route('/proxy')
def proxy():
    """Main proxy endpoint"""
    target_url = request.args.get('url')
    
    if not target_url:
        return "Error: No URL specified", 400
    
    # Validate URL format
    parsed_url = urlparse(target_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return "Error: Invalid URL format", 400
    
    # Check if domain is allowed
    if not is_domain_allowed(target_url):
        return f"Error: Domain not allowed. Allowed domains: {', '.join(ALLOWED_DOMAINS)}", 403
    
    # Fetch content
    response, content = fetch_content(target_url)
    if response is None:
        return f"Error fetching content: {content}", 500
    
    # Determine content type
    content_type = response.headers.get('Content-Type', 'text/html')
    
    # Process content based on type
    if 'text/html' in content_type:
        content = rewrite_urls(content, parsed_url.scheme + '://' + parsed_url.netloc, target_url)
    elif 'javascript' in content_type or 'text/javascript' in content_type:
        content = rewrite_js_content(content, parsed_url.scheme + '://' + parsed_url.netloc)
    
    # Create response
    proxy_response = Response(content)
    
    # Copy relevant headers but filter out problematic ones
    excluded_headers = {
        'content-encoding', 'content-length', 'transfer-encoding',
        'x-frame-options', 'content-security-policy', 'x-content-security-policy',
        'x-webkit-csp', 'strict-transport-security'
    }
    
    for header_name, header_value in response.headers.items():
        if header_name.lower() not in excluded_headers:
            proxy_response.headers[header_name] = header_value
    
    # Add permissive headers
    proxy_response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    proxy_response.headers['Access-Control-Allow-Origin'] = '*'
    
    return proxy_response

if __name__ == '__main__':
    logger.info(f"Starting Web Content Proxy on port {PORT}")
    if SSL_ENABLED and CERT_FILE and KEY_FILE:
        logger.info("SSL enabled")
        app.run(host='0.0.0.0', port=PORT, ssl_context=(CERT_FILE, KEY_FILE), debug=False)
    else:
        app.run(host='0.0.0.0', port=PORT, debug=False)
