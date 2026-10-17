'use client';

import Link from 'next/link';
import { ClayIcon, type ClayIconName } from '@/components/patient/ClayIcon';

/**
 * 三端门厅（黏土拟物风 · 宽屏落地页）。
 * 视觉：云朵小晴 + 草地 + 糖果色卡片；桌面两栏 hero，移动单栏。
 * 图标全部为自绘 SVG（ClayIcon），不使用 emoji。
 */
const portals: Array<{
  href: string;
  icon: ClayIconName;
  tone: 'mint' | 'peach' | 'sky';
  tag: string;
  title: string;
  description: string;
  footer: string;
}> = [
  {
    href: '/student',
    icon: 'student',
    tone: 'mint',
    tag: '给 10–18 岁的你',
    title: '学生端',
    description:
      '和小晴聊聊天，说说最近睡得怎么样、心里有没有堵着的事。不想答的可以跳过。',
    footer: '任务号 + 证件后四位 →',
  },
  {
    href: '/teacher/login',
    icon: 'teacher',
    tone: 'peach',
    tag: '学校 / 机构工作台',
    title: '心理老师端',
    description:
      '建任务、看风险提示、处理求助、复核结论。AI 不下诊断，最后一步永远是人。',
    footer: '工号 + 密码 →',
  },
  {
    href: '/guardian',
    icon: 'guardian',
    tone: 'sky',
    tag: '监护人 / 家长',
    title: '家长端',
    description:
      '需要你知晓的通知会出现在这里：签知情同意、了解学校支持安排。',
    footer: '手机号 + 验证码 →',
  },
];

function XiaoQingClay() {
  return (
    <svg
      viewBox="0 0 520 420"
      className="mx-auto w-full max-w-[520px]"
      role="img"
      aria-label="黏土小晴"
    >
      <defs>
        <radialGradient id="cloudBody" cx="46%" cy="26%" r="82%">
          <stop offset="0%" stopColor="#FFFEFB" />
          <stop offset="62%" stopColor="#FCF7EC" />
          <stop offset="100%" stopColor="#EFE3D1" />
        </radialGradient>
        <radialGradient id="heartGrad" cx="35%" cy="28%" r="80%">
          <stop offset="0%" stopColor="#FF9C8E" />
          <stop offset="100%" stopColor="#E95445" />
        </radialGradient>
        <radialGradient id="sunGrad" cx="35%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#FFE9A6" />
          <stop offset="100%" stopColor="#F5CD55" />
        </radialGradient>
        <filter id="claySoft" x="-30%" y="-30%" width="160%" height="170%">
          <feDropShadow dx="0" dy="12" stdDeviation="14" floodColor="#8A6F4D" floodOpacity="0.16" />
        </filter>
        <filter id="clayTiny" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="5" stdDeviation="6" floodColor="#8A6F4D" floodOpacity="0.18" />
        </filter>
      </defs>

      {/* 地面草地 */}
      <path d="M28 352 Q260 306 492 352 L492 404 Q260 424 28 404 Z" fill="#B7D6A0" />
      <ellipse cx="260" cy="352" rx="212" ry="26" fill="#A9CB93" opacity="0.55" />

      {/* 太阳 */}
      <g filter="url(#clayTiny)">
        <circle cx="452" cy="86" r="30" fill="url(#sunGrad)" />
        <g stroke="#F5CD55" strokeWidth="6" strokeLinecap="round">
          <line x1="452" y1="30" x2="452" y2="16" />
          <line x1="508" y1="86" x2="522" y2="86" />
          <line x1="404" y1="60" x2="394" y2="50" />
          <line x1="500" y1="60" x2="510" y2="50" />
        </g>
      </g>

      {/* 小云 */}
      <g filter="url(#clayTiny)" opacity="0.95">
        <ellipse cx="88" cy="96" rx="44" ry="22" fill="#FFFDF9" />
        <ellipse cx="118" cy="86" rx="26" ry="18" fill="#FFFDF9" />
      </g>

      {/* 云朵小晴 */}
      <g filter="url(#claySoft)">
        <circle cx="152" cy="244" r="62" fill="url(#cloudBody)" />
        <circle cx="300" cy="248" r="58" fill="url(#cloudBody)" />
        <circle cx="228" cy="202" r="82" fill="url(#cloudBody)" />
        <circle cx="180" cy="205" r="52" fill="url(#cloudBody)" />
        <rect x="128" y="228" width="216" height="96" rx="48" fill="url(#cloudBody)" />
      </g>

      {/* 眼睛 */}
      <ellipse cx="206" cy="212" rx="9.5" ry="12" fill="#39322A" />
      <ellipse cx="258" cy="212" rx="9.5" ry="12" fill="#39322A" />
      <circle cx="209.5" cy="207" r="3.2" fill="#FFFDF9" />
      <circle cx="261.5" cy="207" r="3.2" fill="#FFFDF9" />

      {/* 腮红 */}
      <ellipse cx="184" cy="238" rx="14" ry="8.5" fill="#F7B1A4" opacity="0.9" />
      <ellipse cx="282" cy="238" rx="14" ry="8.5" fill="#F7B1A4" opacity="0.9" />

      {/* 微笑 */}
      <path d="M220 238 q11 11 22 0" fill="none" stroke="#39322A" strokeWidth="4" strokeLinecap="round" />

      {/* 手 */}
      <circle cx="162" cy="300" r="17" fill="url(#cloudBody)" filter="url(#clayTiny)" />
      <circle cx="292" cy="300" r="17" fill="url(#cloudBody)" filter="url(#clayTiny)" />

      {/* 爱心 */}
      <path
        d="M227 312 c-20 -18 -44 5 -20 26 l20 18 20 -18 c24 -21 0 -44 -20 -26 z"
        fill="url(#heartGrad)"
        filter="url(#clayTiny)"
      />

      {/* 木牌 */}
      <g filter="url(#clayTiny)">
        <rect x="352" y="258" width="118" height="74" rx="14" fill="#F4DFC0" />
        <rect x="360" y="266" width="102" height="58" rx="10" fill="#FBEFD9" />
        <line x1="411" y1="332" x2="411" y2="372" stroke="#C9A976" strokeWidth="9" strokeLinecap="round" />
        <text x="411" y="291" textAnchor="middle" fontSize="15" fontWeight="900" fill="#8A6F4D">
          慢慢来
        </text>
        <text x="411" y="311" textAnchor="middle" fontSize="13" fontWeight="800" fill="#A98B60">
          也算数
        </text>
      </g>

      {/* 小花 */}
      <g filter="url(#clayTiny)">
        <circle cx="86" cy="340" r="7" fill="#F8D874" />
        <circle cx="74" cy="332" r="6" fill="#FFC4B8" />
        <circle cx="98" cy="332" r="6" fill="#FFC4B8" />
        <circle cx="74" cy="348" r="6" fill="#FFC4B8" />
        <circle cx="98" cy="348" r="6" fill="#FFC4B8" />
      </g>
    </svg>
  );
}

export default function Home() {
  return (
    <div className="patient-app scrollbar-soft">
      <div className="patient-mobile-frame">
        <div className="mx-auto w-full max-w-[1100px] px-6 pb-16 pt-7 md:px-8 md:pt-9">
          {/* 顶部 */}
          <header className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-[var(--accent-mint)] text-lg font-black shadow-[0_8px_18px_rgb(94_78_55_/_0.14)]">
              晴
            </span>
            <div>
              <p className="text-[17px] font-black leading-tight">心晴伙伴</p>
              <p className="text-[11px] font-bold text-foreground-muted">
                青少年心理护航系统
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <Link
                href="/teacher/login"
                className="hidden rounded-full px-4 py-2 text-sm font-bold text-foreground-muted transition hover:bg-surface-secondary md:block"
              >
                老师端
              </Link>
              <Link
                href="/guardian"
                className="hidden rounded-full px-4 py-2 text-sm font-bold text-foreground-muted transition hover:bg-surface-secondary md:block"
              >
                家长端
              </Link>
              <Link
                href="/student"
                className="patient-primary-button min-h-10 px-5 text-sm"
              >
                开始聊天
              </Link>
            </div>
          </header>

          {/* Hero */}
          <section className="mt-10 grid items-center gap-8 md:mt-14 md:grid-cols-[1.08fr_0.92fr] md:gap-12">
            <div>
              <span className="patient-sticker-tag">给 10–18 岁的你</span>
              <h1 className="mt-5 text-[38px] font-black leading-[1.12] md:text-[56px]">
                把心里的石头，
                <br className="hidden md:block" />
                轻轻放下。
              </h1>
              <p className="mt-5 max-w-[34em] text-[15px] font-semibold leading-8 text-foreground-muted md:text-base">
                小晴是陪你聊天的 AI 伙伴——不是老师，不打分，也不给你贴标签。
                说说最近的睡眠、压力、和朋友的小事，聊完由心理老师认真看一眼。
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link href="/student" className="patient-primary-button px-8">
                  开始和小晴聊聊
                </Link>
                <Link href="/teacher/login" className="patient-outline-button px-6">
                  我是老师，去工作台
                </Link>
              </div>
              <p className="mt-4 flex items-center gap-2 text-xs font-bold text-foreground-muted">
                <ClayIcon name="lock" tone="lemon" size={22} />
                聊天内容严格保密；只有涉及安全时，小晴才会告诉心理老师来帮你。
              </p>
            </div>
            <div className="relative">
              <div className="pointer-events-none absolute inset-x-6 top-6 -z-10 h-[78%] rounded-[48px] bg-[var(--accent-sky)] opacity-30 blur-2xl" />
              <XiaoQingClay />
            </div>
          </section>

          {/* 三端入口 */}
          <section className="mt-12 grid gap-5 md:mt-16 md:grid-cols-3">
            {portals.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="patient-card group flex flex-col p-5 transition-transform duration-200 hover:-translate-y-1"
              >
                <div className="flex items-center gap-2.5">
                  <ClayIcon name={item.icon} tone={item.tone} size={46} />
                  <span className="text-[11px] font-black text-foreground-muted">
                    {item.tag}
                  </span>
                </div>
                <h2 className="mt-3 text-[20px] font-black">{item.title}</h2>
                <p className="mt-1.5 flex-1 text-[13px] font-semibold leading-6 text-foreground-muted">
                  {item.description}
                </p>
                <p className="mt-4 text-xs font-black text-foreground-muted">
                  {item.footer}
                </p>
              </Link>
            ))}
          </section>

          {/* 边界声明 */}
          <section className="patient-card-sticker mt-8 flex items-start gap-3 p-5 md:mt-10 md:p-6">
            <ClayIcon name="lock" tone="lemon" size={38} style={{ flexShrink: 0 }} />
            <p className="text-[13px] font-bold leading-7 text-[#6b5a33]">
              我们的边界 —— 学生和小晴的日常对话不会同步给老师或家长；
              只有「安全与求助」信息走保密例外，一切风险提示都由本校心理老师人工处理。
              AI 不下诊断，也不替代专业帮助。
            </p>
          </section>

          <footer className="mt-10 text-center text-[11px] font-bold text-foreground-placeholder">
            心晴伙伴 · 青少年心理护航 · 演示数据为合成档案
          </footer>
        </div>
      </div>
    </div>
  );
}
