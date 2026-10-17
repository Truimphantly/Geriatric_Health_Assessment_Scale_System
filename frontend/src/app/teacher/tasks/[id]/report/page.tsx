'use client';

/**
 * 教师端护航报告页。
 *
 * 作用：按任务查看心理护航报告快照（各量表得分/风险/AI 小结 + 复核说明 + 建议）。
 */

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import NurseLayout from '@/components/layout/NurseLayout';
import { Card, CardTitle } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import { apiRequest } from '@/lib/api/httpClient';

interface ReportScaleRow {
  scale_name: string;
  scale_code: string;
  total_score: number | null;
  risk_level: string | null;
  risk_label: string;
  answered: number;
  total: number;
  ai_summary: string;
}

interface TaskReport {
  task_no: string;
  task_status: string;
  persisted: boolean;
  report_no: string;
  student_name: string;
  overall_risk: string;
  overall_risk_label: string;
  scales: ReportScaleRow[];
  key_findings: string;
  conclusion: string;
  suggestions: string;
  reviewed_by: string;
  reviewed_at: string | null;
}

const RISK_VARIANTS: Record<string, 'success' | 'warning' | 'danger'> = {
  low_risk: 'success',
  medium_risk: 'warning',
  high_risk: 'danger',
  unknown: 'warning',
};

export default function TaskReportPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const taskId = params?.id ?? '';
  const [report, setReport] = useState<TaskReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((signal: AbortSignal) => {
    apiRequest<TaskReport>(`/api/tasks/${encodeURIComponent(taskId)}/report`, {
      signal,
    })
      .then((data) => {
        if (!signal.aborted) setReport(data);
      })
      .catch((cause) => {
        if (!signal.aborted) {
          setError(cause instanceof Error ? cause.message : '加载失败');
        }
      })
      .finally(() => {
        if (!signal.aborted) setLoading(false);
      });
  }, [taskId]);

  useEffect(() => {
    if (!taskId) return;
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [taskId, load]);

  return (
    <NurseLayout wide>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Badge variant="primary">心理护航报告</Badge>
          <h1 className="text-3xl mt-2">
            {report?.student_name || '学生'} · 评估报告
          </h1>
          <p className="text-foreground-muted mt-1">
            任务 {report?.task_no || taskId}
            {report?.reviewed_by ? ` · 复核老师：${report.reviewed_by}` : ''}
          </p>
        </div>
        <button
          type="button"
          onClick={() => router.back()}
          className="rounded-full bg-surface px-4 py-2 text-sm font-semibold text-foreground shadow-sm hover:shadow-md transition-shadow"
        >
          返回
        </button>
      </div>

      {loading ? (
        <Card padding="lg">
          <p className="text-foreground-muted text-center py-12">加载中…</p>
        </Card>
      ) : error ? (
        <Card padding="lg">
          <p className="text-danger text-center py-8">{error}</p>
        </Card>
      ) : report ? (
        <div className="space-y-5">
          <Card padding="lg">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>整体评估</CardTitle>
                <p className="text-sm text-foreground-muted mt-1">
                  {report.persisted
                    ? '教师复核确认后生成的报告快照'
                    : '该任务尚未复核确认，以下为临时快照（不落库）'}
                </p>
              </div>
              <Badge variant={RISK_VARIANTS[report.overall_risk] ?? 'info'} size="lg">
                风险{report.overall_risk_label}
              </Badge>
            </div>
            {report.conclusion && (
              <p className="mt-4 rounded-2xl bg-primary-tint px-4 py-3 text-sm font-semibold text-foreground">
                老师复核说明：{report.conclusion}
              </p>
            )}
            {report.suggestions && (
              <p className="mt-3 rounded-2xl bg-surface-secondary px-4 py-3 text-sm font-semibold text-foreground-muted">
                下一步建议：{report.suggestions}
              </p>
            )}
          </Card>

          <Card padding="lg">
            <CardTitle>量表小结</CardTitle>
            <div className="mt-4 space-y-3">
              {(report.scales ?? []).length === 0 ? (
                <p className="text-foreground-muted text-center py-8">
                  暂无量表结果
                </p>
              ) : (
                (report.scales ?? []).map((row) => (
                  <div
                    key={`${row.scale_code}-${row.scale_name}`}
                    className="rounded-2xl border border-border bg-surface-secondary p-4"
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-bold text-foreground">
                        {row.scale_name}
                      </span>
                      <Badge
                        variant={RISK_VARIANTS[row.risk_level ?? 'unknown'] ?? 'info'}
                        size="sm"
                      >
                        风险{row.risk_label}
                      </Badge>
                      {row.total_score !== null && (
                        <span className="text-sm font-semibold text-foreground">
                          得分 {row.total_score}
                        </span>
                      )}
                      <span className="ml-auto text-xs text-foreground-muted">
                        已答 {row.answered}/{row.total || '-'} 题
                      </span>
                    </div>
                    {row.ai_summary && (
                      <p className="mt-2 text-sm text-foreground-muted leading-6">
                        {row.ai_summary}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>

          {report.key_findings && (
            <Card padding="lg">
              <CardTitle>主要发现</CardTitle>
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground-muted">
                {report.key_findings}
              </p>
            </Card>
          )}

          <p className="text-center text-xs text-foreground-placeholder">
            本报告仅用于校内心理护航参考，不构成医学诊断。
            <Link href="/teacher/risks" className="text-primary underline underline-offset-4">
              查看风险台账
            </Link>
          </p>
        </div>
      ) : null}
    </NurseLayout>
  );
}
