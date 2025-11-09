# CDN Setup Guide

This guide covers setting up a Content Delivery Network (CDN) for frontend assets to improve performance and reduce server load.

## Overview

The CDN setup provides:
- **Global Distribution**: Serve assets from edge locations worldwide
- **Improved Performance**: Reduced latency for users
- **Reduced Server Load**: Offload static asset serving
- **Better Caching**: Aggressive caching for static assets
- **Cost Optimization**: Reduced bandwidth costs

## Supported CDN Providers

### Cloudflare
- Free tier available
- Easy setup with Pages
- Automatic HTTPS
- DDoS protection
- Global edge network

### AWS CloudFront
- Integrated with S3
- Pay-as-you-go pricing
- Custom cache policies
- Lambda@Edge support

## Quick Start

### Cloudflare Pages

1. **Install Wrangler CLI**:
   ```bash
   npm install -g wrangler
   ```

2. **Login to Cloudflare**:
   ```bash
   wrangler login
   ```

3. **Configure Environment Variables**:
   ```bash
   export CLOUDFLARE_ACCOUNT_ID=your_account_id
   export CLOUDFLARE_PROJECT_NAME=swe-platform
   export CDN_URL=https://swe-platform.pages.dev
   ```

4. **Deploy**:
   ```bash
   ./scripts/cdn/deploy-to-cdn.sh
   ```

### AWS CloudFront

1. **Configure AWS Credentials**:
   ```bash
   aws configure
   ```

2. **Set Environment Variables**:
   ```bash
   export AWS_S3_BUCKET=swe-platform-assets
   export AWS_CLOUDFRONT_DISTRIBUTION_ID=your_distribution_id
   export CDN_URL=https://cdn.swe-platform.com
   export CDN_PROVIDER=aws
   ```

3. **Deploy**:
   ```bash
   ./scripts/cdn/deploy-to-cdn.sh
   ```

## Next.js Configuration

### CDN Configuration File

**Location**: `apps/web/next.config.cdn.js`

**Features**:
- Asset prefix for CDN URLs
- Custom image loader for CDN
- Cache headers for static assets
- Webpack public path configuration

### Usage

```bash
# Build with CDN config
cd apps/web
NEXT_CONFIG_FILE=next.config.cdn.js npm run build
```

Or set environment variable:
```bash
export CDN_URL=https://cdn.example.com
npm run build
```

## Cache Headers

### Static Assets
- `/_next/static/*`: `Cache-Control: public, max-age=31536000, immutable`
- `/_next/image/*`: `Cache-Control: public, max-age=31536000, immutable`

### API Routes
- `/api/*`: `Cache-Control: no-cache, no-store, must-revalidate`

### HTML Pages
- `/*`: `Cache-Control: public, max-age=3600`

## Cloudflare Configuration

### Page Rules

1. **Static Assets**:
   - Pattern: `*_next/static/*`
   - Cache Level: Cache Everything
   - Edge Cache TTL: 1 year
   - Browser Cache TTL: 1 year

2. **Images**:
   - Pattern: `*_next/image/*`
   - Cache Level: Cache Everything
   - Edge Cache TTL: 1 year
   - Browser Cache TTL: 1 year

3. **API Routes**:
   - Pattern: `*/api/*`
   - Cache Level: Bypass

### Settings

- **Cache Level**: Aggressive
- **Browser Cache TTL**: 1 year
- **Edge Cache TTL**: 1 year
- **Minify**: CSS, HTML, JS enabled
- **Compression**: Brotli and Gzip enabled
- **HTTP/2**: Enabled
- **HTTP/3**: Enabled
- **0-RTT**: Enabled

## AWS CloudFront Configuration

### Cache Behaviors

1. **Static Assets** (`/_next/static/*`):
   - TTL: 1 year
   - Compress: Yes
   - Forward Cookies: None
   - Forward Query String: No

2. **Images** (`/_next/image/*`):
   - TTL: 1 year
   - Compress: Yes
   - Forward Cookies: None
   - Forward Query String: Yes (for optimization params)

3. **API Routes** (`/api/*`):
   - TTL: 0 (no cache)
   - Compress: Yes
   - Forward Cookies: All
   - Forward Query String: Yes

### Origin Configuration

- **Origin**: Your application server
- **Protocol**: HTTPS only
- **SSL Protocols**: TLS 1.2, TLS 1.3

## Image Optimization

### Custom Image Loader

**Location**: `apps/web/lib/image-loader.js`

Loads images through CDN with optimization parameters:
- Width parameter (`w`)
- Quality parameter (`q`)
- CDN URL prefix

### Usage

```typescript
import Image from 'next/image';

<Image
  src="/image.jpg"
  width={800}
  height={600}
  quality={90}
  loader={cdnImageLoader}
/>
```

## Deployment

### Automated Deployment

The deployment script (`scripts/cdn/deploy-to-cdn.sh`) handles:
1. Building frontend with CDN config
2. Uploading assets to CDN
3. Invalidating cache (if needed)
4. Verifying deployment

### Manual Deployment

#### Cloudflare Pages

```bash
wrangler pages deploy apps/web/.next \
  --project-name=swe-platform \
  --compatibility-date=2025-11-09
```

#### AWS S3 + CloudFront

```bash
# Sync to S3
aws s3 sync apps/web/.next/static s3://bucket/_next/static/ \
  --cache-control "public, max-age=31536000, immutable"

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/_next/static/*"
```

## Monitoring

### Cloudflare Analytics

- Request volume
- Bandwidth usage
- Cache hit ratio
- Response times
- Error rates

### AWS CloudWatch

- Request metrics
- Cache statistics
- Error rates
- Origin latency

## Best Practices

1. **Cache Static Assets Aggressively**: 1 year TTL for immutable assets
2. **Bypass Cache for API**: Never cache API responses
3. **Use Compression**: Enable Brotli and Gzip
4. **Monitor Cache Hit Ratio**: Aim for >90% hit ratio
5. **Set Proper Headers**: Use appropriate Cache-Control headers
6. **Invalidate on Deploy**: Clear cache when deploying updates
7. **Use CDN for Images**: Serve images through CDN with optimization
8. **Monitor Performance**: Track response times and error rates

## Troubleshooting

### Assets Not Loading from CDN

1. **Check CDN URL**: Verify `CDN_URL` environment variable
2. **Check Build Config**: Ensure using `next.config.cdn.js`
3. **Check Cache**: Clear browser and CDN cache
4. **Check CORS**: Verify CORS headers if needed

### Cache Not Updating

1. **Invalidate Cache**: Use CDN invalidation API
2. **Check TTL**: Verify cache TTL settings
3. **Check Headers**: Verify Cache-Control headers
4. **Version Assets**: Use versioned asset paths

### Performance Issues

1. **Check Cache Hit Ratio**: Low hit ratio indicates misconfiguration
2. **Check Origin Latency**: High origin latency affects performance
3. **Check Compression**: Ensure compression is enabled
4. **Check Edge Locations**: Verify edge locations are optimal

## Production Checklist

- [ ] CDN provider configured
- [ ] Next.js CDN config enabled
- [ ] Cache headers configured
- [ ] Image loader configured
- [ ] Deployment script tested
- [ ] Cache invalidation tested
- [ ] Monitoring set up
- [ ] Performance tested
- [ ] Documentation updated

## Related Documentation

- [Next.js Image Optimization](https://nextjs.org/docs/basic-features/image-optimization)
- [Cloudflare Pages](https://developers.cloudflare.com/pages/)
- [AWS CloudFront](https://docs.aws.amazon.com/cloudfront/)
- [Staging Deployment](./STAGING_DEPLOYMENT.md)

## Support

For issues:
1. Check troubleshooting section
2. Review CDN provider logs
3. Verify configuration files
4. Test deployment script
5. Contact platform team

