/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    proxyClientMaxBodySize: '500mb',
    serverActions: {
      bodySizeLimit: '500mb',
    },
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
      {
        source: '/clips/:path*',
        destination: 'http://127.0.0.1:8000/clips/:path*',
      },
      {
        source: '/frames/:path*',
        destination: 'http://127.0.0.1:8000/frames/:path*',
      },
      {
        source: '/exports/:path*',
        destination: 'http://127.0.0.1:8000/exports/:path*',
      },
    ]
  },
}

export default nextConfig
