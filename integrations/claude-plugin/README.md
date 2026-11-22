# Bus Kar! Claude Plugin / Extension Package

This directory contains the ready-to-upload plugin package for Claude Desktop & Claude Organization Catalogs.

## Files
- `plugin.json`: Standard Claude plugin descriptor with all 7 transit tools defined.
- `manifest.json`: Web and connector manifest format.
- `icon.png`: Official Bus Kar transit badge icon (128x128).
- `bus-kar-claude-plugin.zip`: Pre-packaged zip archive for 1-click upload.

## How It Works

### Localhost vs Cloud Endpoint
- **Default (`127.0.0.1:8000`)**: If uploaded as-is, the plugin will connect to your local Bus Kar server running on this computer.
- **For Everyone on the Internet**: Once you deploy Bus Kar to Hugging Face or another cloud host, change the `"url"` in `plugin.json` from `http://127.0.0.1:8000/mcp/sse` to `https://your-app.hf.space/mcp/sse`. Anyone who uploads or installs this plugin will be able to query live Indian buses instantly from anywhere in the world!
