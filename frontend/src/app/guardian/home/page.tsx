'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  acknowledgeReferral,
  fetchGuardianPortal,
  guardianClauses,
  logoutGuardian,
  signGuardianConsent,
  type GuardianConsentClause,
  type GuardianPortal,
  type GuardianReferral,
} from '@/lib/guardian/api';

/** 家长端门户：学生摘要 + 安全提醒 + 转介跟踪 + 知情同意签署。 */
export default function GuardianHomePage() {
  const router = useRouter();
  const [portal, setPortal] = useState<GuardianPortal | null>(null);
  const [error, setError] = useState('');
  const [clauses, setClauses] = useState<GuardianConsentClause[]>(guardianClauses);
  const [signerName, setSignerName] = useState('');
  const [relation, setRelation] = useState('');
  const [consentState, setConsentState] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [referralFeedback, setReferralFeedback] = useState<Record<number, string>>({});
  const [referralBusy, setReferralBusy] = useState<number | null>(null);
  const [referralState, setReferralState] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const next = await fetchGuardianPortal();
        setPortal(next);
        setSignerName(next.guardian.name);
        setRelation(next.guardian.relation);
      } catch {
        router.replace('/guardian');
        setError('登录已失效，请重新用手机号进入');
      }
    };
    void load();
  }, [router]);

  const toggleClause = (code: string) => {
    setClauses((current) =>
      current.map((item) =>
        item.clauseCode === code ? { ...item, confirmed: !item.confirmed } : item
      )
    );
  };

  const submitConsent = async () => {
    if (!signerName.trim()) {
      setConsentState('请填写监护人姓名');
      return;
    }
    if (!clauses.every((item) => item.confirmed)) {
      setConsentState('请逐条确认后再签署');
      return;
    }
    setSubmitting(true);
    setConsentState('');
    try {
      await signGuardianConsent({
        signerName: signerName.trim(),
        relation: relation.trim() || '监护人',
        clauses,
      });
      setConsentState('已签署，学校心理老师会看到这份回执 ✓');
    } catch (signError) {
      setConsentState(
        signError instanceof Error ? signError.message : '签署失败，请重试'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const submitReferralAck = async (referral: GuardianReferral) => {
    setReferralBusy(referral.id);
    setReferralState('');
    try {
      const updated = await acknowledgeReferral(
        referral.id,
        (referralFeedback[referral.id] ?? '').trim()
      );
      setPortal((prev) =>
        prev
          ? {
              ...prev,
              referrals: (prev.referrals ?? []).map((row) =>
                row.id === updated.id ? updated : row
              ),
            }
          : prev
      );
      setReferralState('已确认，老师会看到你的回复 ✓');
    } catch (ackError) {
      setReferralState(
        ackError instanceof Error ? ackError.message : '确认失败，请重试'
      );
    } finally {
      setReferralBusy(null);
    }
  };

  if (!portal) {
    return (
      <div className="patient-app scrollbar-soft">
        <div className="patient-mobile-frame">
          <div className="flex min-h-screen items-center justify-center">
            <p className="font-bold text-foreground-muted">
              {error || '正在加载家长端…'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const priorityTone = (priority: string) =>
    priority === 'urgent' || priority === 'high'
      ? 'border-[#ef6a63] bg-[#ffefee] text-[#a24c46]'
      : 'border-[var(--ink)] bg-[var(--accent-lemon)] text-foreground';

  return (
    <div className="patient-app scrollbar-soft">
      <div className="patient-mobile-frame">
        <header className="patient-topbar patient-topbar-with-right">
          <span />
          <h1 className="patient-topbar-title">家长端</h1>
          <button
            type="button"
            className="patient-touch-button text-sm font-black text-foreground-muted"
            onClick={() => {
              void logoutGuardian().finally(() => router.replace('/guardian'));
            }}
          >
            退出
          </button>
        </header>

        <div className="space-y-4 px-[18px] pb-10 pt-4">
          <section className="patient-card p-5">
            <div className="flex items-center gap-3">
              <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl border-[2.5px] border-[var(--ink)] bg-[var(--accent-sky)] text-[26px]">
                👤
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-[18px] font-black">
                  {portal.guardian.relation} · {portal.guardian.name}
                </p>
                <p className="mt-0.5 text-xs font-semibold text-foreground-muted">
                  登记手机号 {portal.guardian.phone_masked}
                </p>
              </div>
            </div>
            <p className="mt-4 rounded-2xl border-2 border-foreground bg-surface-secondary p-3 text-sm font-bold">
              关联学生：{portal.student.name} ·{' '}
              {portal.encounter?.department ?? '心理护航中心'}
            </p>
          </section>

          <section>
            <h2 className="mb-2 text-[17px] font-black">需要你知晓的提醒</h2>
            {portal.notices.length === 0 ? (
              <div className="patient-card-sticker p-5 text-center">
                <p className="text-[30px]">🌿</p>
                <p className="mt-2 font-black">暂时没有需要你处理的提醒</p>
                <p className="mt-1 text-xs font-semibold text-foreground-muted">
                  只有在出现安全与求助类情况时，学校才会通知你
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {portal.notices.map((notice) => (
                  <article key={notice.id} className="patient-card p-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full border-2 px-2.5 py-0.5 text-[11px] font-black ${priorityTone(notice.priority)}`}
                      >
                        {notice.handled ? '已处理' : '待你配合'}
                      </span>
                      <span className="text-xs font-bold text-foreground-muted">
                        {notice.action_label}
                      </span>
                      <span className="ml-auto text-[11px] font-semibold text-foreground-placeholder">
                        {notice.occurred_at.slice(0, 16).replace('T', ' ')}
                      </span>
                    </div>
                    <p className="mt-2.5 text-[15px] font-black">{notice.title}</p>
                    <p className="mt-1.5 text-[13px] font-semibold leading-6 text-foreground-muted">
                      {notice.reason_summary}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-[17px] font-black">转介跟踪</h2>
            {(portal.referrals ?? []).length === 0 ? (
              <div className="patient-card-sticker p-5 text-center">
                <p className="mt-2 font-black">暂时没有转介安排</p>
                <p className="mt-1 text-xs font-semibold text-foreground-muted">
                  若老师建议孩子接受校内辅导或校外专业支持，会在这里说明去向与原因
                </p>
              </div>
            ) : (
              (portal.referrals ?? []).map((referral) => (
                <article key={referral.id} className="patient-card p-4">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full border-2 px-2.5 py-0.5 text-[11px] font-black ${
                        referral.status === 'pending'
                          ? 'border-[#ef6a63] bg-[#ffefee] text-[#a24c46]'
                          : referral.status === 'acknowledged'
                            ? 'border-[var(--ink)] bg-[var(--accent-sky)] text-foreground'
                            : 'border-[var(--ink)] bg-[var(--accent-mint)] text-foreground'
                      }`}
                    >
                      {referral.status === 'pending'
                        ? '待你确认'
                        : referral.status === 'acknowledged'
                          ? '已确认·进行中'
                          : '已完成'}
                    </span>
                    <span className="ml-auto text-[11px] font-semibold text-foreground-placeholder">
                      {(referral.create_time ?? '').slice(0, 16).replace('T', ' ')}
                    </span>
                  </div>
                  <p className="mt-2.5 text-[15px] font-black">
                    转介建议：{referral.target_name}
                  </p>
                  {referral.suggestion && (
                    <p className="mt-1.5 text-[13px] font-semibold leading-6 text-foreground-muted">
                      {referral.suggestion}
                    </p>
                  )}
                  {referral.contact && (
                    <p className="mt-1 text-[13px] font-semibold text-foreground-muted">
                      联系方式：{referral.contact}
                    </p>
                  )}
                  {referral.guardian_feedback && (
                    <p className="mt-2 rounded-xl bg-surface-secondary px-3 py-2 text-xs font-bold">
                      我的回复：{referral.guardian_feedback}
                    </p>
                  )}
                  {referral.status === 'pending' && (
                    <div className="mt-3 space-y-2">
                      <input
                        value={referralFeedback[referral.id] ?? ''}
                        onChange={(event) =>
                          setReferralFeedback((prev) => ({
                            ...prev,
                            [referral.id]: event.target.value,
                          }))
                        }
                        placeholder="可以留言，例如：已收到，这周带孩子去"
                        className="patient-field w-full px-3 text-sm font-bold outline-none"
                      />
                      <button
                        type="button"
                        disabled={referralBusy === referral.id}
                        onClick={() => void submitReferralAck(referral)}
                        className="patient-primary-button w-full justify-center"
                      >
                        {referralBusy === referral.id ? '正在确认…' : '我已知晓 ✓'}
                      </button>
                    </div>
                  )}
                </article>
              ))
            )}
            {referralState && (
              <p className="rounded-xl border-2 border-dashed border-[var(--ink)] bg-[var(--accent-lemon)] px-3 py-2 text-xs font-black">
                {referralState}
              </p>
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-[17px] font-black">知情同意（4 条）</h2>
            {clauses.map((item) => (
              <button
                key={item.clauseCode}
                type="button"
                onClick={() => toggleClause(item.clauseCode)}
                className={`w-full rounded-2xl border-[2.5px] p-3.5 text-left transition ${
                  item.confirmed
                    ? 'border-[var(--ink)] bg-[var(--accent-mint)] shadow-[3px_3px_0_var(--ink)]'
                    : 'border-foreground bg-surface'
                }`}
                aria-pressed={item.confirmed}
              >
                <span className="flex items-center gap-2 text-sm font-black">
                  {item.confirmed ? '✓ ' : ''}
                  {item.clauseName}
                  <span className="ml-auto rounded-full border-2 border-[var(--ink)] px-2 py-0.5 text-[10px] font-black">
                    {item.importanceLevel === 'critical' ? '必须' : '重要'}
                  </span>
                </span>
                <span className="mt-1.5 block text-xs font-semibold leading-5 text-foreground-muted">
                  {item.guardianContent}
                </span>
              </button>
            ))}

            <div className="patient-card space-y-3 p-4">
              <label className="block">
                <span className="text-xs font-black text-foreground-muted">
                  监护人姓名
                </span>
                <input
                  value={signerName}
                  onChange={(event) => setSignerName(event.target.value)}
                  className="patient-field mt-1.5 w-full px-3 text-sm font-bold outline-none"
                />
              </label>
              <label className="block">
                <span className="text-xs font-black text-foreground-muted">
                  与学生关系
                </span>
                <input
                  value={relation}
                  onChange={(event) => setRelation(event.target.value)}
                  className="patient-field mt-1.5 w-full px-3 text-sm font-bold outline-none"
                />
              </label>
              {consentState && (
                <p className="rounded-xl border-2 border-dashed border-[var(--ink)] bg-[var(--accent-lemon)] px-3 py-2 text-xs font-black">
                  {consentState}
                </p>
              )}
              <button
                type="button"
                disabled={submitting}
                onClick={() => void submitConsent()}
                className="patient-primary-button w-full justify-center"
              >
                {submitting ? '正在提交…' : '确认并签署 ✓'}
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
