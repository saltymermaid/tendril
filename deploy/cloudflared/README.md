# Cloudflare Tunnel Setup for Tendril

## Overview

Tendril uses a Cloudflare Tunnel to expose the application securely over HTTPS
without opening any inbound ports on the Beelink server. All traffic flows
through Cloudflare's network, providing DDoS protection and SSL termination.

## Setup Steps

### 1. Create the Tunnel

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to **Networks → Tunnels**
3. Click **Create a tunnel**
4. Name it `tendril`
5. Copy the tunnel token

### 2. Configure the Tunnel

In the Cloudflare dashboard, add a **Public Hostname**:

| Field | Value |
|-------|-------|
| Subdomain | (leave empty for apex) |
| Domain | `tendril.garden` |
| Type | HTTP |
| URL | `frontend:80` |

### 3. Set the Token

Add the tunnel token to your `.env` file:

```env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiYWJj...
```

### 4. Start with Tunnel

```bash
docker compose -f docker-compose.prod.yml --profile tunnel up -d
```

## DNS Configuration

Ensure your domain's DNS is managed by Cloudflare:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `@` | `<tunnel-id>.cfargotunnel.com` | Proxied ☁️ |
| CNAME | `www` | `tendril.garden` | Proxied ☁️ |

> The CNAME records are automatically created when you add the public hostname
> in the Cloudflare dashboard.

## SSL/TLS Settings

In Cloudflare Dashboard → SSL/TLS:

- **Encryption mode**: Full (strict)
- **Always Use HTTPS**: On
- **Minimum TLS Version**: 1.2
- **Automatic HTTPS Rewrites**: On

## Troubleshooting

```bash
# Check tunnel status
docker compose -f docker-compose.prod.yml --profile tunnel logs cloudflared

# Restart tunnel
docker compose -f docker-compose.prod.yml --profile tunnel restart cloudflared

# Test connectivity
curl -v https://tendril.garden/api/health
```
