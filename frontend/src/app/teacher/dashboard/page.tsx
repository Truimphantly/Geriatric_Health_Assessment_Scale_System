'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import NurseLayout from '@/components/layout/NurseLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import TaskCard from '@/components/task/TaskCard';
import { useUserStore } from '@/lib/stores/useUserStore';
import { useTaskStore } from '@/lib/stores/useTaskStore';
import { runtimeConfig } from '@/lib/runtime/config';
import { listRisks } from '@/lib/riskLedger';
import {
  ClipboardDocumentListIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  FlagIcon,
} from '@heroicons/react/24/outline';

export default function NurseDashboardPage() {
  const { user } = useUserStore();
  const tasks = useTaskStore((state) => state.tasks);
  const [riskSummary, setRiskSummary] = useState({ open: 0, highOrAbove: 0 });

  // 统计数据
  const stats = {
    total: tasks.length,
    pending: tasks.filter((t) => t.taskStatus === 'pending').length,
    inProgress: tasks.filter((t) => t.taskStatus === 'in_progress').length,
    pendingReview: tasks.filter((t) => t.taskStatus === 'pending_review').length,
    completed: tasks.filter((t) => t.taskStatus === 'completed').length,
  };

  // 我的任务（分配给当前心理老师的）
  const myTasks = tasks.filter((t) => t.assignedNurseId === user?.id);

  // 风险台账摘要（API 模式下拉取未结案数量）
  useEffect(() => {
    if (runtimeConfig.dataMode !== 'api') return;
    const controller = new AbortController();
    listRisks({ status: 'open' }, controller.signal)
      .then((result) => {
        setRiskSummary({
          open: result.stats.open,
          highOrAbove: result.stats.highOrAbove,
        });
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  return (
    <NurseLayout>
      {/* 欢迎信息 */}
      <div className="mb-8">
        <h1 className="text-3xl font-sans font-extrabold text-foreground mb-2">
          您好，<span className="text-primary italic">{user?.name}</span>
        </h1>
        <p className="text-foreground-muted">今天有 {myTasks.length} 项待处理任务</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card hover padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground-muted mb-1">总任务数</p>
              <p className="text-3xl font-sans font-extrabold text-foreground">{stats.total}</p>
            </div>
            <div className="p-3 bg-primary-tint rounded-xl">
              <ClipboardDocumentListIcon className="w-6 h-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card hover padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground-muted mb-1">待开始</p>
              <p className="text-3xl font-sans font-extrabold text-foreground">{stats.pending}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-xl">
              <ClockIcon className="w-6 h-6 text-info" />
            </div>
          </div>
        </Card>

        <Card hover padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground-muted mb-1">待审核</p>
              <p className="text-3xl font-sans font-extrabold text-foreground">
                {stats.pendingReview}
              </p>
            </div>
            <div className="p-3 bg-amber-50 rounded-xl">
              <ExclamationCircleIcon className="w-6 h-6 text-warning" />
            </div>
          </div>
        </Card>

        <Card hover padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground-muted mb-1">已完成</p>
              <p className="text-3xl font-sans font-extrabold text-foreground">{stats.completed}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-xl">
              <CheckCircleIcon className="w-6 h-6 text-success" />
            </div>
          </div>
        </Card>
      </div>

      {/* 我的任务列表 */}
      <Card padding="lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>我的任务</CardTitle>
              <CardDescription>分配给我的心理评估任务</CardDescription>
            </div>
            <div className="flex items-center gap-3">
              {riskSummary.open > 0 && (
                <Link
                  href="/teacher/risks"
                  className="flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 text-sm font-semibold text-warning hover:shadow-sm transition-shadow"
                >
                  <FlagIcon className="w-4 h-4" />
                  {riskSummary.open} 条风险待跟进
                  {riskSummary.highOrAbove > 0 && `（含高及以上 ${riskSummary.highOrAbove} 条）`}
                </Link>
              )}
              <Badge variant="primary">{myTasks.length} 项</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {myTasks.length === 0 ? (
            <div className="text-center py-12">
              <ClipboardDocumentListIcon className="w-16 h-16 text-foreground-muted mx-auto mb-4 opacity-50" />
              <p className="text-foreground-muted">暂无任务</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {myTasks.map((task) => (
                <TaskCard key={task.id} task={task} href={`/teacher/tasks/${task.id}`} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </NurseLayout>
  );
}
