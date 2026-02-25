/** @type {import('next').NextConfig} */
const nextConfig = {
    // Required for the production Docker image (node server.js)
    output: "standalone",

    async rewrites() {
        // In Docker, NEXT_PUBLIC_API_URL is set to http://backend:8000
        // In local dev, it falls back to http://localhost:8000 (configurable via ENV)
        const apiBase =
            process.env.NEXT_PUBLIC_API_URL || `http://${process.env.BACKEND_HOST || 'localhost'}:${process.env.BACKEND_PORT || '8000'}`;
        return [
            {
                source: "/api/:path*",
                destination: `${apiBase}/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
