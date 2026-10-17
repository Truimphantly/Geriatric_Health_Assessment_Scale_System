'use client';

/**
 * 小晴官方立绘组件（ComfyUI 生图 → 清洗裁边 PNG）。
 *
 * 作用：替换手绘占位 SVG。支持九种表情切换与轻浮动动画；
 *       动画尊重系统 prefers-reduced-motion（globals.css 中处理）。
 */

import Image from 'next/image';
import type { CSSProperties } from 'react';

export type XiaoQingExpression =
  | 'default'
  | 'transparent'
  | 'listen'
  | 'cheer'
  | 'comfort'
  | 'whisper'
  | 'empathy'
  | 'help'
  | 'energy'
  | 'night';

const ART: Record<XiaoQingExpression, { src: string; width: number; height: number }> = {
  default: { src: '/xiaoqing/xq-01-default.png', width: 640, height: 513 },
  transparent: { src: '/xiaoqing/xq-00-transparent.png', width: 640, height: 586 },
  listen: { src: '/xiaoqing/xq-02-listen.png', width: 640, height: 604 },
  cheer: { src: '/xiaoqing/xq-03-cheer.png', width: 618, height: 640 },
  comfort: { src: '/xiaoqing/xq-04-comfort.png', width: 640, height: 552 },
  whisper: { src: '/xiaoqing/xq-05-whisper.png', width: 640, height: 502 },
  empathy: { src: '/xiaoqing/xq-06-empathy.png', width: 640, height: 512 },
  help: { src: '/xiaoqing/xq-07-help.png', width: 603, height: 640 },
  energy: { src: '/xiaoqing/xq-08-energy.png', width: 640, height: 593 },
  night: { src: '/xiaoqing/xq-09-night.png', width: 640, height: 594 },
};

interface XiaoQingArtProps {
  expression?: XiaoQingExpression;
  /** 显示宽度 px（.xq-hero 之类由调用方样式控制时可省略） */
  size?: number;
  className?: string;
  style?: CSSProperties;
  /** 是否启用轻浮动动画（默认开） */
  float?: boolean;
}

export default function XiaoQingArt({
  expression = 'default',
  size,
  className = '',
  style,
  float = true,
}: XiaoQingArtProps) {
  const art = ART[expression];
  const widthStyle = size !== undefined ? `${size}px` : undefined;
  return (
    <Image
      src={art.src}
      alt="小晴"
      width={art.width}
      height={art.height}
      draggable={false}
      className={`xq-art ${float ? 'xq-float' : ''} ${className}`}
      style={{
        width: widthStyle,
        height: 'auto',
        ...style,
      }}
    />
  );
}
