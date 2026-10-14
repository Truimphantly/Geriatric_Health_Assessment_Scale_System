import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { NetworkStatus } from '@/components/shared/NetworkStatus';
import './globals.css';

export const metadata: Metadata = {
  title: '心晴伙伴·青少年心理护航',
  description: '青少年心理健康对话式评估：小晴陪伴聊天、风险提示与心理老师复核',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <NetworkStatus />
        {children}
      </body>
    </html>
  );
}
