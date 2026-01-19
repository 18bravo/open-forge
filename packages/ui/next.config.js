/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Enable experimental features for App Router
  experimental: {
    typedRoutes: true,
  },

  // Image optimization configuration
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Environment variables that should be available on the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Webpack configuration for any custom needs
  webpack: (config, { isServer }) => {
    // Add any custom webpack configuration here
    return config;
  },

  // Headers for security and CORS
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Redirects configuration
  async redirects() {
    return [];
  },

  // Rewrites for API proxying (optional)
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [],
      fallback: [],
    };
  },
};

module.exports = nextConfig;
