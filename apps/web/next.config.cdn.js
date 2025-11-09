/**
 * Next.js Configuration for CDN Deployment
 * 
 * Optimizes build for CDN distribution with proper cache headers
 * and asset optimization.
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output configuration for static export (if using static hosting)
  // output: 'export', // Uncomment if using static export
  
  // Asset prefix for CDN
  assetPrefix: process.env.CDN_URL || '',
  
  // Image optimization
  images: {
    // Configure image domains for CDN
    domains: [
      process.env.CDN_DOMAIN || '',
      'images.unsplash.com',
      'via.placeholder.com',
    ],
    // Use CDN for image optimization
    loader: process.env.CDN_URL ? 'custom' : 'default',
    loaderFile: process.env.CDN_URL ? './lib/image-loader.js' : undefined,
  },
  
  // Compression
  compress: true,
  
  // Production optimizations
  productionBrowserSourceMaps: false,
  
  // Headers for CDN caching
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/image/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },
    ];
  },
  
  // Webpack configuration for CDN
  webpack: (config, { isServer }) => {
    if (!isServer && process.env.CDN_URL) {
      // Replace public path with CDN URL
      config.output.publicPath = `${process.env.CDN_URL}/_next/`;
    }
    return config;
  },
  
  // Environment variables
  env: {
    CDN_URL: process.env.CDN_URL || '',
    CDN_DOMAIN: process.env.CDN_DOMAIN || '',
  },
};

module.exports = nextConfig;

