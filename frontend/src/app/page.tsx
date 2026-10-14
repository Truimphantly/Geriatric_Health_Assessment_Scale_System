'use client';

import Link from 'next/link';

/**
 * 三端门厅：学生 / 心理老师 / 家长三个入口。
 * 与设计样机（design_mockups/a-full/login.html）同一皮肤语言。
 */
const portals = [
  {
    href: '/student',
    emoji: '🙋',
    tag: '和中学生',
    title: '学生端',
    description:
      '和小晴聊天了解最近的状态 · 情绪手账 · 需要时把求助信息递给心理老师。',
    footer: '任务号 + 证件后四位，或扫码 →',
    tone: 'bg-[var(--accent-mint)]',
  },
  {
    href: '/teacher/login',
    emoji: '🧑‍🏫',
    tag: '学校 / 机构工作台',
    title: '心理老师端',
    description:
      '建任务、看风险提示、处理求助、复核结论。AI 不下诊断，最后一步永远是人。',
    footer: '工号 + 密码 →',
    tone: 'bg-[var(--accent-peach)]',
  },
  {
    href: '/guardian',
    emoji: '🏠',
    tag: '监护人 / 家长',
    title: '家长端',
    description:
      '收到需要监护人知晓的通知时进来：签知情同意、了解学校支持安排。',
    footer: '手机号 + 短信验证码 →',
    tone: 'bg-[var(--accent-sky)]',
  },
] as const;

export default function Home() {
  return (
    <div className="patient-app scrollbar-soft">
      <div className="patient-mobile-frame">
        <div className="px-[20px] pb-10 pt-12">
          <div className="text-center">
            <svg
              className="mx-auto h-24 w-24"
              viewBox="0 0 200 200"
              aria-label="小晴"
              role="img"
            >
              <circle cx="100" cy="100" r="96" fill="#FFF9F2" stroke="#2A2320" strokeWidth="4" />
              <circle cx="70" cy="90" r="9" fill="#2A2320" />
              <circle cx="130" cy="90" r="9" fill="#2A2320" />
              <circle cx="73" cy="86" r="3" fill="#FFF9F2" />
              <circle cx="133" cy="86" r="3" fill="#FFF9F2" />
              <ellipse cx="52" cy="114" rx="10" ry="6.5" fill="#FFB5A7" />
              <ellipse cx="148" cy="114" rx="10" ry="6.5" fill="#FFB5A7" />
              <path d="M84 110 q16 13 32 2" fill="none" stroke="#2A2320" strokeWidth="4" strokeLinecap="round" />
              <circle cx="100" cy="34" r="9" fill="#7FDBB6" stroke="#2A2320" strokeWidth="3" />
              <line x1="100" y1="43" x2="100" y2="56" stroke="#2A2320" strokeWidth="3" />
            </svg>
            <h1 className="mt-4 text-[27px] font-black leading-tight">
              心晴伙伴
              <span className="mt-1 block text-[17px] text-foreground-muted">
                青少年心理护航系统
              </span>
            </h1>
            <p className="mt-3 text-sm font-bold text-foreground-muted">
              选择你的入口
            </p>
          </div>

          <div className="mt-7 space-y-5">
            {portals.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-[22px] border-[2.5px] border-[var(--ink)] bg-surface p-5 shadow-[6px_6px_0_var(--ink)] transition hover:-translate-x-0.5 hover:-translate-y-0.5"
              >
                <span className={`patient-sticker-tag ${item.tone}`}>
                  {item.tag}
                </span>
                <span className="mt-3 flex items-center gap-3">
                  <span className="text-[34px]">{item.emoji}</span>
                  <span>
                    <span className="block text-[21px] font-black">
                      {item.title}
                    </span>
                    <span className="mt-1 block text-xs font-semibold leading-5 text-foreground-muted">
                      {item.description}
                    </span>
                  </span>
                </span>
                <span className="mt-3 block text-xs font-black text-foreground-muted">
                  {item.footer}
                </span>
              </Link>
            ))}
          </div>

          <div className="mt-7 rounded-2xl border-[2.5px] border-[var(--ink)] bg-[var(--accent-lemon)] p-4 shadow-[4px_4px_0_var(--ink)]">
            <p className="text-xs font-bold leading-6 text-[#4a3f10]">
              🔒 我们的边界：学生和小晴的日常对话不会同步给老师或家长；
              只有安全与求助信息走保密例外，一切风险提示交由本校心理老师人工处理。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
