'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginGuardian, sendGuardianCode } from '@/lib/guardian/api';

/**
 * 家长端登录：手机号 + 短信验证码。
 * 演示环境不接运营商短信，后端回显固定校验码 123456。
 */
export default function GuardianLoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [hint, setHint] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    setError('');
    setHint('');
    try {
      const result = await sendGuardianCode(phone.trim());
      setHint(
        result.demo_code
          ? `演示环境验证码：${result.demo_code}（5 分钟内有效）`
          : '验证码已发送，请查看短信'
      );
    } catch (sendError) {
      setError(
        sendError instanceof Error ? sendError.message : '发送失败，请确认手机号'
      );
    }
  };

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await loginGuardian(phone.trim(), code.trim());
      router.push('/guardian/home');
    } catch (loginError) {
      setError(
        loginError instanceof Error ? loginError.message : '登录失败，请重试'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="patient-app scrollbar-soft">
      <div className="patient-mobile-frame">
        <div className="px-[20px] pb-8 pt-12">
          <div className="text-center">
            <span className="mx-auto grid h-[86px] w-[86px] place-items-center rounded-[28px] border-[2.5px] border-[var(--ink)] bg-[var(--accent-sky)] text-[40px] shadow-[5px_5px_0_var(--ink)]">
              🏠
            </span>
            <h1 className="mt-5 text-[28px] font-black leading-tight">家长端</h1>
            <p className="mt-2 text-sm font-semibold text-foreground-muted">
              收到需要你知晓的通知时，用登记手机号进来
            </p>
          </div>

          <form onSubmit={handleLogin} className="mt-7 space-y-4">
            <label className="patient-field flex items-center gap-3 px-4">
              <span className="text-[17px]">📱</span>
              <span className="shrink-0 text-[16px] font-black">手机号</span>
              <input
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="学生档案里登记的号码"
                inputMode="numeric"
                maxLength={20}
                className="min-w-0 flex-1 bg-transparent text-[15px] font-bold outline-none placeholder:font-medium placeholder:text-foreground-placeholder"
                required
              />
            </label>

            <label className="patient-field flex items-center gap-3 px-4">
              <span className="text-[17px]">✉️</span>
              <span className="shrink-0 text-[16px] font-black">验证码</span>
              <input
                value={code}
                onChange={(event) => setCode(event.target.value)}
                placeholder="6 位验证码"
                inputMode="numeric"
                maxLength={6}
                className="min-w-0 flex-1 bg-transparent text-[15px] font-bold outline-none placeholder:font-medium placeholder:text-foreground-placeholder"
                required
              />
              <button
                type="button"
                onClick={() => void handleSend()}
                className="shrink-0 rounded-full border-2 border-[var(--ink)] bg-[var(--accent-lemon)] px-3.5 py-2 text-xs font-black shadow-[2px_2px_0_var(--ink)]"
              >
                获取验证码
              </button>
            </label>

            {hint && (
              <div className="rounded-2xl border-2 border-dashed border-[var(--ink)] bg-[var(--accent-mint)] px-4 py-3 text-sm font-bold">
                {hint}
              </div>
            )}
            {error && (
              <div
                role="alert"
                className="rounded-2xl border-2 border-[#ef6a63] bg-[#ffefee] px-4 py-3 text-sm font-semibold text-[#a24c46]"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="patient-primary-button w-full justify-center"
            >
              {loading ? '正在核验…' : '查看我的通知 →'}
            </button>
          </form>

          <div className="mt-6 rounded-2xl border-2 border-foreground bg-[var(--accent-peach)] p-4 text-left shadow-[3px_3px_0_var(--ink)]">
            <p className="text-sm font-black">家长端能看到什么</p>
            <p className="mt-1.5 text-xs font-semibold leading-5 text-[#5a3a34]">
              发生什么、需要你配合什么。孩子的日记与小晴的日常对话原文不会转发——
              看到的是「需要你做什么」，而不是「孩子说了什么」。
            </p>
          </div>

          <p className="mt-5 text-center text-xs font-bold text-foreground-muted">
            号码来自孩子档案的监护人登记项 · 仅法律监护人可绑定
          </p>
        </div>
      </div>
    </div>
  );
}
