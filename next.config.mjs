/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false, // Changed to false to catch TypeScript errors
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    typedRoutes: true,
  },
}

export default nextConfig
