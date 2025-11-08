/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@ai-company/shared'],
  experimental: {
    serverActions: true,
  },
}

module.exports = nextConfig
