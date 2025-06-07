# AI Derivation Server

A simple Flask web server for handling AI derivation requests.

## Endpoints

- `GET /hash?req=<request>` - Takes a request parameter and returns a hash-like string
- `GET /drv?hash=<hash>` - Takes a hash parameter and returns a derivation result string

## Running with Nix

To build and run the server:

```bash
# Build the server
nix build .#ai-drv-server

# Run the server
./result/bin/ai-drv-server
```

The server will start on `http://localhost:5000`.

## Development

For development with a Nix shell:

```bash
# Enter the development shell
nix develop .#dev-shell

# Run the server directly
python -m ai_drv_server.app
```

## Testing

You can test the endpoints using curl:

```bash
# Test the /hash endpoint
curl "http://localhost:5000/hash?req=test"

# Test the /drv endpoint  
curl "http://localhost:5000/drv?hash=abc123"
```

Or use the provided test script:

```bash
python test_server.py
``` 