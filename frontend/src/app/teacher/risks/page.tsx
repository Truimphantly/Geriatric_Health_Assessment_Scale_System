'use client';

/**
 * 风险台账页。
 *
 * 作用：教师查看学生风险档案（危机上报/学生呼叫/关键词兜底汇总），
 *       流转状态（待跟进→跟进中→已转介/已结案）、调整等级、追加跟进记录。
 */

import { useCallback, useEffect, useState } from 'react';
import NurseLayout from '@/components/layout/NurseLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import { runtimeConfig } from '@/lib/runtime/config';
import {
  REFERRAL_STATUS_LABEL,
  REFERRAL_TARGET_LABEL,
  RISK_LEVEL_LABEL,
  RISK_SOURCE_LABEL,
  RISK_STATUS_LABEL,
  completeReferral,
  createReferral,
  listRisks,
  listRiskReferrals,
  updateRisk,
  type ReferralItem,
  type RiskItem,
  type RiskLevel,
  type RiskListData,
  type RiskStatus,
} from '@/lib/riskLedger';
import {
  ArrowPathIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  FlagIcon,
} from '@heroicons/react/24/outline';

const STATUS_VARIANTS: Record<RiskStatus, 'warning' | 'info' | 'primary' | 'success'> = {
  open: 'warning',
  following: 'info',
  referred: 'primary',
  closed: 'success',
};

const LEVEL_VARIANTS: Record<RiskLevel, 'success' | 'warning' | 'danger'> = {
  low: 'success',
  medium: 'warning',
  high: 'danger',
  critical: 'danger',
};

const NEXT_STATUS_OPTIONS: Record<RiskStatus, RiskStatus[]> = {
  open: ['following', 'referred', 'closed'],
  following: ['referred', 'closed'],
  referred: ['closed'],
  closed: [],
};

function fetchRisks(
  statusFilter: RiskStatus | '',
  signal: AbortSignal,
  onDone: (result: RiskListData) => void,
  onError: (message: string) => void,
  onSettled: () => void
): void {
  listRisks(statusFilter ? { status: statusFilter } : {}, signal)
    .then((result) => {
      if (!signal.aborted) onDone(result);
    })
    .catch((cause) => {
      if (!signal.aborted) {
        onError(cause instanceof Error ? cause.message : '加载失败');
      }
    })
    .finally(() => {
      if (!signal.aborted) onSettled();
    });
}

export default function TeacherRisksPage() {
  const [data, setData] = useState<RiskListData | null>(null);
  const [loading, setLoading] = useState(runtimeConfig.dataMode === 'api');
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});
  const [statusFilter, setStatusFilter] = useState<RiskStatus | ''>('');
  const apiMode = runtimeConfig.dataMode === 'api';

  // 转介相关状态
  const [referralFormFor, setReferralFormFor] = useState<number | null>(null);
  const [referralDraft, setReferralDraft] = useState({
    targetType: 'school_counseling',
    targetName: '',
    contact: '',
    suggestion: '',
  });
  const [referralLists, setReferralLists] = useState<Record<number, ReferralItem[]>>(
    {}
  );
  const [referralError, setReferralError] = useState<string | null>(null);

  const loadReferrals = useCallback((riskId: number) => {
    listRiskReferrals(riskId)
      .then((rows) =>
        setReferralLists((prev) => ({ ...prev, [riskId]: rows }))
      )
      .catch((cause) =>
        setReferralError(
          cause instanceof Error ? cause.message : '转介单加载失败'
        )
      );
  }, []);

  const refresh = useCallback(
    (signal: AbortSignal) => {
      fetchRisks(
        statusFilter,
        signal,
        setData,
        setError,
        () => setLoading(false)
      );
    },
    [statusFilter]
  );

  useEffect(() => {
    if (!apiMode) return;
    const controller = new AbortController();
    refresh(controller.signal);
    return () => controller.abort();
  }, [apiMode, refresh]);

  const handleUpdate = async (
    item: RiskItem,
    input: { status?: RiskStatus; level?: RiskLevel; note?: string }
  ) => {
    setBusyId(item.id);
    try {
      const updated = await updateRisk(item.id, input);
      setData((prev) =>
        prev
          ? {
              stats: prev.stats,
              items: prev.items.map((row) => (row.id === updated.id ? updated : row)),
            }
          : prev
      );
      setNoteDrafts((prev) => ({ ...prev, [item.id]: '' }));
      refresh(new AbortController().signal);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '更新失败');
    } finally {
      setBusyId(null);
    }
  };

  const items = data?.items ?? [];
  const stats = data?.stats;

  const submitReferral = async (item: RiskItem) => {
    if (!referralDraft.targetName.trim()) {
      setReferralError('请填写转介去向名称');
      return;
    }
    setBusyId(item.id);
    setReferralError(null);
    try {
      await createReferral(item.id, {
        targetType: referralDraft.targetType,
        targetName: referralDraft.targetName.trim(),
        contact: referralDraft.contact.trim(),
        suggestion: referralDraft.suggestion.trim(),
      });
      setReferralFormFor(null);
      setReferralDraft({
        targetType: 'school_counseling',
        targetName: '',
        contact: '',
        suggestion: '',
      });
      loadReferrals(item.id);
      refresh(new AbortController().signal);
    } catch (cause) {
      setReferralError(cause instanceof Error ? cause.message : '转介失败');
    } finally {
      setBusyId(null);
    }
  };

  const finishReferral = async (item: RiskItem, referral: ReferralItem) => {
    setBusyId(item.id);
    setReferralError(null);
    try {
      await completeReferral(referral.id);
      loadReferrals(item.id);
      refresh(new AbortController().signal);
    } catch (cause) {
      setReferralError(cause instanceof Error ? cause.message : '完成失败');
    } finally {
      setBusyId(null);
    }
  };

  const toggleReferralForm = (item: RiskItem) => {
    if (referralFormFor === item.id) {
      setReferralFormFor(null);
      return;
    }
    setReferralDraft({
      targetType: 'school_counseling',
      targetName: '',
      contact: '',
      suggestion: '',
    });
    setReferralFormFor(item.id);
    loadReferrals(item.id);
  };

  return (
    <NurseLayout>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Badge variant="danger">安全护航</Badge>
          <h1 className="text-3xl mt-2">
            风险<span className="text-primary italic">台账</span>
          </h1>
          <p className="text-foreground-muted mt-1">
            汇总每次危机上报与学生呼叫，等级只升不降，处理后留跟进记录
          </p>
        </div>
        {apiMode && (
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              refresh(new AbortController().signal);
            }}
            className="flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold text-foreground bg-surface shadow-sm hover:shadow-md transition-shadow"
          >
            <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
        )}
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {(
            [
              { label: '待跟进', value: stats.open, icon: FlagIcon, tone: 'bg-amber-50 text-warning' },
              { label: '跟进中', value: stats.following, icon: ChatBubbleLeftRightIcon, tone: 'bg-blue-50 text-info' },
              { label: '已转介', value: stats.referred, icon: ArrowPathIcon, tone: 'bg-primary-tint text-primary' },
              { label: '高及以上', value: stats.highOrAbove, icon: ExclamationTriangleIcon, tone: 'bg-red-50 text-danger' },
            ] as const
          ).map((card) => (
            <Card key={card.label} hover padding="md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground-muted mb-1">{card.label}</p>
                  <p className="text-3xl font-sans font-extrabold text-foreground">
                    {card.value}
                  </p>
                </div>
                <div className={`p-3 rounded-xl ${card.tone}`}>
                  <card.icon className="w-6 h-6" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {!apiMode ? (
        <Card padding="lg">
          <p className="text-foreground-muted text-center py-12">
            风险台账需要后端数据（API 模式），当前为演示原型模式
          </p>
        </Card>
      ) : error || referralError ? (
        <Card padding="lg">
          <p className="text-danger text-center py-8">{error ?? referralError}</p>
          <div className="text-center">
            <button
              type="button"
              onClick={() => refresh(new AbortController().signal)}
              className="text-primary underline underline-offset-4"
            >
              重试
            </button>
          </div>
        </Card>
      ) : (
        <Card padding="lg">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>学生风险档案</CardTitle>
                <CardDescription>按学生汇总，新档案在前</CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                {(['', 'open', 'following', 'referred', 'closed'] as const).map((value) => (
                  <button
                    key={value || 'all'}
                    type="button"
                    onClick={() => setStatusFilter(value)}
                    className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                      statusFilter === value
                        ? 'bg-primary text-white'
                        : 'bg-surface-secondary text-foreground-muted hover:text-foreground'
                    }`}
                  >
                    {value === '' ? '全部' : RISK_STATUS_LABEL[value]}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading && items.length === 0 ? (
              <p className="text-foreground-muted text-center py-12">加载中…</p>
            ) : items.length === 0 ? (
              <div className="text-center py-12">
                <ExclamationTriangleIcon className="w-16 h-16 text-foreground-muted mx-auto mb-4 opacity-50" />
                <p className="text-foreground-muted">暂无风险档案</p>
                <p className="text-sm text-foreground-muted mt-1">
                  学生对话中出现危机信号时会自动登记到这里
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-2xl border border-border bg-surface p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <Badge variant={LEVEL_VARIANTS[item.level]} size="sm">
                          {RISK_LEVEL_LABEL[item.level]}风险
                        </Badge>
                        <span className="font-semibold text-foreground">
                          {item.studentName}
                        </span>
                        {item.studentNo && (
                          <span className="text-sm text-foreground-muted">
                            {item.studentNo}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={STATUS_VARIANTS[item.status]} size="sm">
                          {RISK_STATUS_LABEL[item.status]}
                        </Badge>
                        <Badge variant="default" size="sm">
                          {RISK_SOURCE_LABEL[item.source] ?? item.source}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-sm text-foreground mt-3 whitespace-pre-line">
                      {item.reason || '（无描述）'}
                    </p>

                    {item.followUps.length > 0 && (
                      <ul className="mt-3 space-y-1 text-sm text-foreground-muted">
                        {item.followUps.slice(-5).map((entry, index) => (
                          <li key={`${item.id}-${index}`}>
                            · {entry.time.replace('T', ' ').slice(0, 16)}{' '}
                            {entry.by}：{entry.note || entry.action}
                          </li>
                        ))}
                      </ul>
                    )}

                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      {item.status !== 'closed' && (
                        <button
                          type="button"
                          disabled={busyId === item.id}
                          onClick={() => toggleReferralForm(item)}
                          className={`rounded-full px-4 py-1.5 text-sm font-semibold ${
                            referralFormFor === item.id
                              ? 'bg-primary text-white'
                              : 'border border-primary text-primary'
                          } disabled:opacity-50`}
                        >
                          发起转介
                        </button>
                      )}
                      {NEXT_STATUS_OPTIONS[item.status].map((next) => (
                        <button
                          key={next}
                          type="button"
                          disabled={busyId === item.id}
                          onClick={() => void handleUpdate(item, { status: next })}
                          className={`rounded-full px-4 py-1.5 text-sm font-semibold text-white bg-primary disabled:opacity-50 ${
                            next === 'closed' ? 'opacity-80' : ''
                          }`}
                        >
                          流转至「{RISK_STATUS_LABEL[next]}」
                        </button>
                      ))}
                      {item.level !== 'critical' && (
                        <button
                          type="button"
                          disabled={busyId === item.id}
                          onClick={() =>
                            void handleUpdate(item, { level: 'critical' })
                          }
                          className="rounded-full px-4 py-1.5 text-sm font-semibold text-danger border border-danger disabled:opacity-50"
                        >
                          提升为极高
                        </button>
                      )}
                    </div>

                    {referralFormFor === item.id && (
                      <div className="mt-3 space-y-2 rounded-2xl border border-primary/30 bg-primary-tint/40 p-4">
                        <p className="text-sm font-bold text-foreground">
                          发起转介（家长端会同步展示并可确认知悉）
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(REFERRAL_TARGET_LABEL).map(
                            ([value, label]) => (
                              <button
                                key={value}
                                type="button"
                                onClick={() =>
                                  setReferralDraft((prev) => ({
                                    ...prev,
                                    targetType: value,
                                  }))
                                }
                                className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
                                  referralDraft.targetType === value
                                    ? 'bg-primary text-white'
                                    : 'bg-surface border border-border text-foreground-muted'
                                }`}
                              >
                                {label}
                              </button>
                            )
                          )}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          <input
                            value={referralDraft.targetName}
                            onChange={(event) =>
                              setReferralDraft((prev) => ({
                                ...prev,
                                targetName: event.target.value,
                              }))
                            }
                            placeholder="去向名称，例如：校心理辅导室（周一至周五）"
                            className="rounded-xl border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/30"
                          />
                          <input
                            value={referralDraft.contact}
                            onChange={(event) =>
                              setReferralDraft((prev) => ({
                                ...prev,
                                contact: event.target.value,
                              }))
                            }
                            placeholder="联系方式（选填）"
                            className="rounded-xl border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/30"
                          />
                        </div>
                        <textarea
                          value={referralDraft.suggestion}
                          onChange={(event) =>
                            setReferralDraft((prev) => ({
                              ...prev,
                              suggestion: event.target.value,
                            }))
                          }
                          rows={2}
                          placeholder="给家长的建议，例如：建议一周两次谈话，先从睡眠聊起"
                          className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/30"
                        />
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            disabled={
                              busyId === item.id ||
                              !referralDraft.targetName.trim()
                            }
                            onClick={() => void submitReferral(item)}
                            className="rounded-full bg-primary px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
                          >
                            提交转介
                          </button>
                          <button
                            type="button"
                            onClick={() => setReferralFormFor(null)}
                            className="rounded-full px-4 py-2 text-sm font-semibold text-foreground-muted"
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    )}

                    {(referralLists[item.id] ?? []).length > 0 && (
                      <div className="mt-3 space-y-2">
                        {(referralLists[item.id] ?? []).map((referral) => (
                          <div
                            key={referral.id}
                            className="rounded-xl border border-border bg-surface-secondary p-3 text-sm"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-semibold text-foreground">
                                {REFERRAL_TARGET_LABEL[referral.targetType] ??
                                  referral.targetType}
                              </span>
                              <span className="text-foreground-muted">
                                {referral.targetName}
                              </span>
                              <Badge
                                variant={
                                  referral.status === 'completed'
                                    ? 'success'
                                    : referral.status === 'acknowledged'
                                      ? 'info'
                                      : 'warning'
                                }
                                size="sm"
                              >
                                {REFERRAL_STATUS_LABEL[referral.status]}
                              </Badge>
                              <span className="ml-auto text-[11px] text-foreground-muted">
                                {(referral.createTime ?? '').slice(0, 16).replace('T', ' ')}
                              </span>
                            </div>
                            {referral.suggestion && (
                              <p className="mt-1 text-foreground-muted">
                                建议：{referral.suggestion}
                              </p>
                            )}
                            {referral.guardianFeedback && (
                              <p className="mt-1 font-semibold text-foreground">
                                家长回复：{referral.guardianFeedback}
                              </p>
                            )}
                            {referral.status === 'acknowledged' && (
                              <button
                                type="button"
                                disabled={busyId === item.id}
                                onClick={() => void finishReferral(item, referral)}
                                className="mt-2 rounded-full bg-primary px-4 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                              >
                                确认转介完成（档案结案）
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-3 flex gap-2">
                      <input
                        value={noteDrafts[item.id] ?? ''}
                        onChange={(event) =>
                          setNoteDrafts((prev) => ({
                            ...prev,
                            [item.id]: event.target.value,
                          }))
                        }
                        placeholder="追加跟进记录，例如：已与家长沟通 / 已约面谈"
                        className="flex-1 rounded-xl border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/30"
                      />
                      <button
                        type="button"
                        disabled={busyId === item.id || !(noteDrafts[item.id] ?? '').trim()}
                        onClick={() =>
                          void handleUpdate(item, {
                            note: (noteDrafts[item.id] ?? '').trim(),
                          })
                        }
                        className="rounded-xl px-4 py-2 text-sm font-semibold text-primary disabled:opacity-40"
                      >
                        记录
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </NurseLayout>
  );
}
