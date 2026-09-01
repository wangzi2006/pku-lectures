import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://wangzi2006.github.io/pku-lectures/'),
  title: '未名讲座｜未来十四天，值得去现场',
  description:
    '聚合北京大学及骑行可达范围内的公开讲座，经来源核验、去重与人工审核后呈现。',
  icons: {
    icon: '/pku-lectures/favicon.svg',
  },
  openGraph: {
    title: '未名讲座｜未来十四天，值得去现场',
    description: '聚合北京大学及骑行可达范围内，经人工审核的公开讲座。',
    locale: 'zh_CN',
    siteName: '未名讲座',
    type: 'website',
    url: 'https://wangzi2006.github.io/pku-lectures/',
    images: [
      {
        url: '/pku-lectures/og.png',
        width: 1733,
        height: 909,
        alt: '未名讲座：未来十四天，值得去现场',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: '未名讲座｜未来十四天，值得去现场',
    description: '聚合北京大学及骑行可达范围内，经人工审核的公开讲座。',
    images: ['/pku-lectures/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
