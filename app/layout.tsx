import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://wangzi2006.github.io/pku-lectures/'),
  title: '未名讲座｜北大及周边未来 14 天讲座',
  description:
    '北京大学校内及东门骑行约 30 分钟范围内，经审核发布的未来 14 天公开讲座。',
  icons: {
    icon: '/pku-lectures/favicon.svg',
  },
  openGraph: {
    title: '未名讲座｜北大及周边未来 14 天讲座',
    description: '北京大学校内及周边，经审核发布的未来 14 天公开讲座。',
    locale: 'zh_CN',
    siteName: '未名讲座',
    type: 'website',
    url: 'https://wangzi2006.github.io/pku-lectures/',
    images: [
      {
        url: '/pku-lectures/og.png',
        width: 1733,
        height: 909,
        alt: '未名讲座：北大及周边未来 14 天讲座',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: '未名讲座｜北大及周边未来 14 天讲座',
    description: '北京大学校内及周边，经审核发布的未来 14 天公开讲座。',
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
