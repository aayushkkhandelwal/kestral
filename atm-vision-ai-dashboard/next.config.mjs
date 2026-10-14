/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  allowedDevOrigins: [
    '192.168.2.105',
    'localhost',
    '127.0.0.1',
  ],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/results/:path*',
        destination: 'http://127.0.0.1:8000/results/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://127.0.0.1:8000/uploads/:path*',
      },
    ]
  },
}

export default nextConfig
