const backendUrl = (process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

const nextConfig = {
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
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/results/:path*',
        destination: `${backendUrl}/results/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${backendUrl}/uploads/:path*`,
      },
      {
        source: '/clips/:path*',
        destination: `${backendUrl}/clips/:path*`,
      },
      {
        source: '/frames/:path*',
        destination: `${backendUrl}/frames/:path*`,
      },
      {
        source: '/exports/:path*',
        destination: `${backendUrl}/exports/:path*`,
      },
    ]
  },
}

export default nextConfig
