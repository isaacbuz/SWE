# SSL/TLS Certificate Setup Guide

This guide covers setting up SSL/TLS certificates for the SWE Platform using Let's Encrypt.

## Overview

The SSL/TLS setup provides:
- **Let's Encrypt Integration**: Free, automated SSL certificates
- **Automatic Renewal**: Certificates renew automatically
- **HTTPS Enforcement**: All HTTP traffic redirected to HTTPS
- **Security Headers**: HSTS and other security headers configured
- **OCSP Stapling**: Improved certificate validation performance

## Prerequisites

- Domain name configured and pointing to your server
- Ports 80 and 443 open in firewall
- Docker and Docker Compose installed
- Certbot installed (or use Docker image)

## Quick Start

### 1. Set Environment Variables

```bash
export DOMAIN=yourdomain.com
export EMAIL=admin@yourdomain.com
export WWW_DOMAIN=www.yourdomain.com  # Optional
```

### 2. Run Certificate Setup

```bash
# Make scripts executable
chmod +x scripts/ssl/setup-certificates.sh
chmod +x scripts/ssl/renew-certificates.sh

# Run setup (staging for testing)
STAGING=true ./scripts/ssl/setup-certificates.sh

# Run setup (production)
./scripts/ssl/setup-certificates.sh
```

### 3. Update Nginx Configuration

Update `nginx/nginx-https.conf` and `nginx/nginx-ssl.conf` with your domain:

```nginx
# In nginx-https.conf
server_name yourdomain.com www.yourdomain.com;

# In nginx-ssl.conf
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
```

### 4. Start Services

```bash
docker-compose -f docker-compose.ssl.yml up -d
```

## Manual Setup

### Using Certbot Directly

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email
```

### Using Docker

```bash
docker run -it --rm \
  -v ./certbot/conf:/etc/letsencrypt \
  -v ./certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email
```

## Certificate Renewal

### Automatic Renewal

Certificates are automatically renewed via cron job:

```bash
# Check renewal status
sudo certbot renew --dry-run

# Manual renewal
sudo certbot renew
```

### Using Renewal Script

```bash
# Renew certificates
./scripts/ssl/renew-certificates.sh

# Check certificate expiry
./scripts/ssl/renew-certificates.sh yourdomain.com
```

### Docker Renewal

Add to cron or systemd timer:

```bash
# Renew certificates
docker run --rm \
  -v ./certbot/conf:/etc/letsencrypt \
  -v ./certbot/www:/var/www/certbot \
  certbot/certbot renew

# Reload Nginx
docker-compose -f docker-compose.ssl.yml exec nginx nginx -s reload
```

## Nginx Configuration

### SSL Configuration

The SSL configuration (`nginx/nginx-ssl.conf`) includes:
- TLS 1.2 and 1.3 protocols
- Modern cipher suites
- OCSP stapling
- Security headers (HSTS, X-Frame-Options, etc.)

### HTTPS Server

The HTTPS server configuration (`nginx/nginx-https.conf`) includes:
- HTTP to HTTPS redirect
- Let's Encrypt challenge handling
- Proxy configuration for services
- WebSocket support

## Security Headers

The following security headers are configured:

- **Strict-Transport-Security**: Enforces HTTPS
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-XSS-Protection**: XSS protection
- **Referrer-Policy**: Controls referrer information
- **Content-Security-Policy**: XSS and injection protection

## Certificate Locations

- **Certificates**: `/etc/letsencrypt/live/yourdomain.com/`
  - `fullchain.pem`: Certificate chain
  - `privkey.pem`: Private key
  - `chain.pem`: Intermediate certificate
  - `cert.pem`: Certificate only

- **Archive**: `/etc/letsencrypt/archive/yourdomain.com/`
  - Historical certificate versions

- **Renewal Config**: `/etc/letsencrypt/renewal/yourdomain.com.conf`
  - Renewal configuration

## Troubleshooting

### Certificate Not Obtained

1. **Check DNS**: Ensure domain points to your server
   ```bash
   dig yourdomain.com
   ```

2. **Check Ports**: Ensure ports 80 and 443 are open
   ```bash
   sudo netstat -tuln | grep -E '80|443'
   ```

3. **Check Webroot**: Ensure webroot is accessible
   ```bash
   curl http://yourdomain.com/.well-known/acme-challenge/test
   ```

4. **Check Logs**: Review certbot logs
   ```bash
   sudo tail -f /var/log/letsencrypt/letsencrypt.log
   ```

### Certificate Not Renewing

1. **Check Cron**: Verify cron job is running
   ```bash
   sudo crontab -l
   ```

2. **Test Renewal**: Run dry-run test
   ```bash
   sudo certbot renew --dry-run
   ```

3. **Check Expiry**: Verify certificate expiration
   ```bash
   sudo openssl x509 -enddate -noout -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem
   ```

### Nginx Not Loading Certificates

1. **Check Paths**: Verify certificate paths in Nginx config
2. **Check Permissions**: Ensure Nginx can read certificates
   ```bash
   sudo ls -la /etc/letsencrypt/live/yourdomain.com/
   ```

3. **Test Configuration**: Test Nginx configuration
   ```bash
   docker-compose exec nginx nginx -t
   ```

### HTTPS Not Working

1. **Check Firewall**: Ensure port 443 is open
2. **Check Nginx**: Verify Nginx is listening on 443
   ```bash
   docker-compose exec nginx netstat -tuln | grep 443
   ```

3. **Check Certificates**: Verify certificates are valid
   ```bash
   openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
   ```

## Best Practices

1. **Use Staging First**: Test with Let's Encrypt staging environment
2. **Monitor Expiry**: Set up monitoring for certificate expiration
3. **Automate Renewal**: Use cron or systemd for automatic renewal
4. **Backup Certificates**: Regularly backup certificate files
5. **Monitor Logs**: Regularly check certbot and Nginx logs
6. **Update Regularly**: Keep certbot and Nginx updated

## Production Checklist

- [ ] Domain DNS configured correctly
- [ ] Ports 80 and 443 open in firewall
- [ ] Certificates obtained successfully
- [ ] Nginx configured with certificates
- [ ] HTTPS redirect working
- [ ] Security headers configured
- [ ] Automatic renewal set up
- [ ] Certificate expiry monitoring configured
- [ ] Backup strategy for certificates
- [ ] Documentation updated

## Related Documentation

- [Staging Deployment](./STAGING_DEPLOYMENT.md)
- [Security Guide](./SECURITY.md)
- [Production Deployment](./PRODUCTION_DEPLOYMENT.md)

## Support

For issues:
1. Check troubleshooting section
2. Review certbot logs
3. Check Nginx error logs
4. Verify DNS and firewall settings
5. Contact platform team

