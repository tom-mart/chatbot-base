import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Disable strict linting during build (warnings won't fail the build)
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  typescript: {
    // Allow production builds to complete even with type errors
    ignoreBuildErrors: true,
  },
  
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
  // Disable Turbopack to use standard webpack with PostCSS
  experimental: {
    turbo: undefined,
  },
  // Disable compression to allow streaming
  compress: false,
  
  // Proxy API requests to the backend (development only)
  async rewrites() {
    // Only use rewrites in development
    if (process.env.NODE_ENV === 'development') {
      // Use environment variable for backend URL, fallback to localhost:8080
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      return [
        {
          source: '/api/:path*',
          destination: `${backendUrl}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
