import type { NextConfig } from 'next';

const onGitHubPages = process.env.GITHUB_PAGES === 'true';

const nextConfig: NextConfig = {
  output: 'export',
  assetPrefix: onGitHubPages ? '/pku-lectures/' : undefined,
  trailingSlash: true,
};

export default nextConfig;
