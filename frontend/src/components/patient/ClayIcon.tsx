'use client';

import type { CSSProperties, ReactElement } from 'react';

/**
 * 黏土风图标：糖果色圆底 + 顶部内高光 + 线条符号（不使用 emoji）。
 * 用于学生端门厅、任务卡、首页快捷入口等位置。
 */
export type ClayIconName =
  | 'student'
  | 'teacher'
  | 'guardian'
  | 'chat'
  | 'clock'
  | 'heart'
  | 'lock'
  | 'tasks'
  | 'assistant'
  | 'moon'
  | 'edit'
  | 'mail'
  | 'leaf'
  | 'check'
  | 'school';

type Tone = 'mint' | 'peach' | 'sky' | 'lemon' | 'plain';

const TONES: Record<Tone, { base: string; light: string }> = {
  mint: { base: '#8FD5B5', light: '#C9EFDC' },
  peach: { base: '#F6A48F', light: '#FFD9CF' },
  sky: { base: '#9CCBE4', light: '#D8EDF8' },
  lemon: { base: '#EFC85C', light: '#FCEBB4' },
  plain: { base: '#E7DCCB', light: '#F7F0E4' },
};

const SYMBOLS: Record<ClayIconName, ReactElement> = {
  student: (
    <>
      <circle cx="32" cy="34" r="3.1" fill="currentColor" />
      <circle cx="44" cy="34" r="3.1" fill="currentColor" />
      <path d="M34 43q6 5.5 12 0" fill="none" stroke="currentColor" strokeWidth="3.4" strokeLinecap="round" />
    </>
  ),
  teacher: (
    <>
      <rect x="22" y="24" width="28" height="17" rx="4" fill="none" stroke="currentColor" strokeWidth="3.2" />
      <path d="M27 30h10M27 35h16" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" />
      <path d="M32 47h8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </>
  ),
  guardian: (
    <>
      <path d="M32 22l14 11v15a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4V33z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
      <path d="M28 52v-9h8v9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" />
    </>
  ),
  chat: (
    <>
      <path d="M20 28a8 8 0 0 1 8-8h16a8 8 0 0 1 8 8v9a8 8 0 0 1-8 8H33l-8 7v-7a8 8 0 0 1-5-7.5z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
      <circle cx="29" cy="32" r="2" fill="currentColor" />
      <circle cx="37" cy="32" r="2" fill="currentColor" />
      <circle cx="45" cy="32" r="2" fill="currentColor" />
    </>
  ),
  clock: (
    <>
      <circle cx="32" cy="34" r="13" fill="none" stroke="currentColor" strokeWidth="3.2" />
      <path d="M32 26v9l6 4" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" />
    </>
  ),
  heart: (
    <path d="M32 48l-11-9.6C14 32.6 18.6 24 26.4 24c3.1 0 5 1.9 5.6 3.1.6-1.2 2.5-3.1 5.6-3.1 7.8 0 12.4 8.6 5.4 14.4z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
  ),
  lock: (
    <>
      <rect x="23" y="32" width="18" height="15" rx="4" fill="none" stroke="currentColor" strokeWidth="3.2" />
      <path d="M27 32v-4a5 5 0 0 1 10 0v4" fill="none" stroke="currentColor" strokeWidth="3.2" />
      <circle cx="32" cy="39" r="2.2" fill="currentColor" />
    </>
  ),
  tasks: (
    <>
      <path d="M25 27l3 3 5-5" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 39h16M24 46h12" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      <path d="M25 36l3 3 5-5" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  assistant: (
    <>
      <path d="M18 38a7 7 0 0 1 4-13 9 9 0 0 1 17-4 8 8 0 0 1 7 13" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" />
      <circle cx="28" cy="35" r="2.2" fill="currentColor" />
      <circle cx="38" cy="35" r="2.2" fill="currentColor" />
      <path d="M30 41q3 2.6 6 0" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" />
    </>
  ),
  moon: (
    <path d="M38 21a14 14 0 1 0 10 22 12 12 0 0 1-10-22z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
  ),
  edit: (
    <>
      <path d="M24 43l16-16 5 5-16 16-6.5 1.5z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
      <path d="M37 24l5 5" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" />
    </>
  ),
  mail: (
    <>
      <rect x="20" y="25" width="24" height="17" rx="4" fill="none" stroke="currentColor" strokeWidth="3.2" />
      <path d="M21 27l11 9 11-9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" />
    </>
  ),
  leaf: (
    <>
      <path d="M42 22c-14 1-21 9-20 21 12 1 20-6 21-21z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
      <path d="M25 43c5-7 11-12 17-15" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" />
    </>
  ),
  check: <path d="M23 34l6 7 13-13" fill="none" stroke="currentColor" strokeWidth="3.6" strokeLinecap="round" strokeLinejoin="round" />,
  school: (
    <>
      <path d="M32 20l15 8-15 8-15-8z" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
      <path d="M23 33v11c0 3 18 3 18 0V33" fill="none" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" />
      <path d="M47 28v9" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" />
    </>
  ),
};

export function ClayIcon({
  name,
  tone = 'mint',
  size = 44,
  className,
  style,
}: {
  name: ClayIconName;
  tone?: Tone;
  size?: number;
  className?: string;
  style?: CSSProperties;
}) {
  const colors = TONES[tone];
  const gradientId = `clay-${name}-${tone}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      style={style}
      role="img"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id={gradientId} cx="34%" cy="24%" r="86%">
          <stop offset="0%" stopColor={colors.light} />
          <stop offset="100%" stopColor={colors.base} />
        </radialGradient>
      </defs>
      <rect x="2" y="2" width="60" height="60" rx="20" fill={`url(#${gradientId})`} />
      <rect
        x="6"
        y="6"
        width="52"
        height="22"
        rx="16"
        fill="none"
        stroke="rgb(255 255 255 / 55%)"
        strokeWidth="3"
      />
      <g style={{ color: '#4A4036' }}>{SYMBOLS[name]}</g>
    </svg>
  );
}
