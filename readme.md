# Web Content Proxy - Home Assistant Addon

A Home Assistant addon that provides a web proxy service to bypass CORS restrictions and X-Frame-Options headers, allowing you to embed external web content that would otherwise be blocked.

## Features

- **CORS Bypass**: Access content that blocks cross-origin requests
- **Header Filtering**: Removes restrictive headers like X-Frame-Options and Content-Security-Policy  
- **URL Rewriting**: Automatically rewrites URLs in HTML content to route through the proxy
- **JavaScript Handling**: Basic rewriting of dynamic JavaScript URLs
- **Domain Restrictions**: Optional whitelist of allowed domains for security
- **SSL Support**: Optional SSL/TLS encryption
- **Content Size Limits**: Configurable maximum content size to prevent abuse

## Installation

### Method 1: Add Repository to Home Assistant

1. In Home Assistant, go to **Supervisor** → **Add-on Store**
2. Click the menu (three dots) in the top right corner
3. Select **Repositories**
4. Add this repository URL: `https://github.com/yourusername/ha-web-proxy-addon`
5. Click **Add**
6. Find "Web Content Proxy" in the addon store and click **Install**

### Method 2: Manual Installation

1. Navigate to your Home Assistant `addons` directory
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ha-web-proxy-addon.git web_content_proxy
   ```
3. Restart Home Assistant
4. The addon will appear in your local addon store

## Configuration

```yaml
port: 8099                    # Port to run the proxy server on
ssl: false                    # Enable SSL/TLS
certfile: fullchain.pem       # SSL certificate file (if ssl: true)
keyfile: privkey.pem          # SSL private key file (if ssl: true)
allowed_domains: []           # List of allowed domains (empty = allow all)
max_content_size: 10485760    # Maximum content size in bytes (10MB default)
timeout: 30                   # Request timeout in seconds
```

### Example Configuration

```yaml
port: 8099
ssl: false
allowed_domains:
  - "example.com"
  - "trusted-site.org"
max_content_size: 5242880
timeout: 15
```

## Usage

1. Start the addon
2. Access the web interface at `http://homeassistant.local:8099`
3. Enter a URL you want to proxy and click "Load"
4. The content will be served through the proxy with restrictive headers removed

### Direct URL Access

You can also access proxied content directly using:
```
http://homeassistant.local:8099/proxy?url=https://example.com
```

### Embedding in Lovelace

Use the Webpage card in Lovelace to embed proxied content:

```yaml
type: iframe
url: http://homeassistant.local:8099/proxy?url=https://example.com
aspect_ratio: 16:9
```

## Security Considerations

- **Domain Restrictions**: Always configure `allowed_domains` in production to prevent abuse
- **Network Access**: The addon needs internet access to fetch external content
- **Content Filtering**: The addon removes security headers - only proxy trusted content
- **SSL**: Enable SSL in production environments
- **Firewall**: Consider restricting access to the proxy port from external networks

## Troubleshooting

### Addon Won't Start
- Check the logs in the Home Assistant addon page
- Verify the port isn't already in use
- Ensure SSL certificates exist if SSL is enabled

### Content Not Loading
- Check if the target domain is in the allowed_domains list
- Verify the target URL is accessible from your Home Assistant instance
- Check addon logs for error messages
- Ensure content size is under the configured limit

### JavaScript Not Working
- Some JavaScript functionality may not work due to URL rewriting
- Complex single-page applications may have issues
- Check browser console for JavaScript errors

## Development

### File Structure
```
web_content_proxy/
├── config.yaml          # Addon configuration
├── build.yaml           # Multi-architecture build config
├── Dockerfile           # Container build instructions
├── run.sh              # Startup script
├── proxy_server.py     # Main Python application
├── README.md           # Documentation
└── CHANGELOG.md        # Version history
```

### Building Locally

```bash
docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18" -t web-proxy-addon .
```

### Testing

1. Install the addon in development mode
2. Configure with test domains
3. Test various content types (HTML, CSS, JavaScript, images)
4. Verify URL rewriting works correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
