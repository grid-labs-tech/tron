# K3s Manifests Directory

This directory contains Kubernetes manifests that will be automatically applied by k3s when the server starts.

## How it works

K3s automatically applies any YAML files placed in `/var/lib/rancher/k3s/server/manifests/` during server initialization. This directory is mounted as a volume in the docker-compose configuration, allowing you to add manifests that will be automatically loaded.

## Usage

Simply place any Kubernetes manifest YAML files in this directory, and they will be automatically applied when k3s starts.

### Example: Installing Gateway API CRDs

To install Gateway API CRDs automatically, you can download and place them here:

```bash
# Download Gateway API CRDs
curl -L https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml -o docker/manifests/gateway-api-crds.yaml

# Or for experimental resources (TCPRoute, UDPRoute)
curl -L https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/experimental-install.yaml -o docker/manifests/gateway-api-experimental.yaml
```

After placing the files, restart the k3s-server container:

```bash
docker compose -f docker/docker-compose.yaml restart k3s-server
```

## Important Notes

- Files in this directory are applied automatically on k3s startup
- Manifests are applied in alphabetical order
- If you need to remove a manifest, delete the file and restart k3s-server
- Changes to manifests require a k3s-server restart to take effect

