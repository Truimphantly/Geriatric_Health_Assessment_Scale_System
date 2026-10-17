'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import PatientLayout from '@/components/layout/PatientLayout';
import { PatientIcon } from '@/components/patient/PatientIcon';
import { PatientState } from '@/components/patient/PatientState';
import { ClayIcon } from '@/components/patient/ClayIcon';
import { abortRequest, isRequestCancelled } from '@/lib/api/httpClient';
import { groupPatientTasks } from '@/lib/patient/taskGroups';
import { careRepository } from '@/lib/repositories';
import { runtimeConfig } from '@/lib/runtime/config';
import { useTaskStore } from '@/lib/stores/useTaskStore';
import { useUserStore } from '@/lib/stores/useUserStore';
import type { CareTask } from '@/lib/types';

const statusLabels: Record<CareTask['taskStatus'], string> = {
  pending: '待开始',
  in_progress: '进行中',
  pending_review: '等待老师复核',
  completed: '已完成',
  cancelled: '已取消',
};

export default function PatientTasksPage() {
  const router = useRouter();
  const user = useUserStore((state) => state.user);
  const hasHydrated = useUserStore((state) => state.hasHydrated);
  const allTasks = useTaskStore((state) => state.tasks);
  const setTasks = useTaskStore((state) => state.setTasks);
  const [loadError, setLoadError] = useState('');
  const tasks = allTasks.filter((task) => task.patientId === user?.id);
  const taskGroups = groupPatientTasks(tasks);

  useEffect(() => {
    if (runtimeConfig.dataMode !== 'api' || !hasHydrated) return;
    if (!user) {
      router.replace('/student');
      return;
    }

    const controller = new AbortController();
    // API 模式先清理旧浏览器快照，避免后台准备中的任务在请求完成前短暂可见。
    setTasks([]);
    const loadTasks = async () => {
      try {
        const nextTasks = await careRepository.listPatientTasks(
          controller.signal
        );
        setTasks(nextTasks);
        setLoadError('');
      } catch (error) {
        if (controller.signal.aborted || isRequestCancelled(error)) return;
        setLoadError(error instanceof Error ? error.message : '任务加载失败');
      }
    };
    void loadTasks();
    const timer = window.setInterval(() => {
      void loadTasks();
    }, 3000);
    return () => {
      window.clearInterval(timer);
      abortRequest(controller);
    };
  }, [hasHydrated, router, setTasks, user]);

  const renderActiveTask = (task: CareTask) => {
    const current = task.progress?.current ?? 0;
    const total = task.progress?.total ?? 15;
    const percentage = Math.round((current / Math.max(total, 1)) * 100);

    return (
      <article key={task.id} className="patient-card-soft relative p-4">
        <div className="flex items-start gap-3">
          <ClayIcon
            name={task.collectionMode === 'ai_dialogue' ? 'chat' : 'tasks'}
            tone="sky"
            size={48}
            className="shrink-0"
          />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-[20px] font-black">和小晴聊聊近况</h2>
              <span className="rounded-full bg-[var(--accent-lemon)] px-2.5 py-1 text-xs font-black shadow-[inset_0_2px_0_rgb(255_255_255_/_70%),0_4px_10px_rgb(94_78_55_/_0.12)]">
                {task.collectionMode === 'ai_dialogue' ? '聊天式' : '填表式'}
              </span>
            </div>
            <p className="mt-1 text-sm font-semibold text-foreground-muted">
              像聊天一样，大约 10 分钟
            </p>
          </div>
          <span aria-hidden="true" className="mt-0.5 text-3xl font-black leading-none text-foreground-placeholder">
            ›
          </span>
        </div>

        {task.handoffRequired && (
          <div className="mt-3 flex items-start gap-2.5 rounded-2xl bg-[#ffefee] p-3 text-sm font-semibold leading-6 text-[#a24c46] shadow-[inset_0_2px_0_rgb(255_255_255_/_60%),0_8px_18px_rgb(228_87_76_/_12%)]">
            <ClayIcon name="teacher" tone="peach" size={26} className="shrink-0" />
            心理老师正在处理一个重要的提醒（今天）。可以先休息，有事随时呼叫。
          </div>
        )}

        <div className="mt-4 pl-[60px]">
          <div className="flex items-end justify-between">
            <p className="text-[16px] font-bold">
              <span className="text-[25px] text-primary">{current}</span>
              <span className="mx-1 text-foreground-muted">/</span>
              {total}
            </p>
            <span className="rounded-full bg-[var(--accent-sky)] px-3 py-1.5 text-xs font-black shadow-[inset_0_2px_0_rgb(255_255_255_/_70%),0_4px_10px_rgb(94_78_55_/_0.12)]">
              {statusLabels[task.taskStatus]}
            </span>
          </div>
          <div className="patient-progress-track mt-2">
            <div
              className="patient-progress-value"
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground-muted">
              <PatientIcon name="clock" className="h-[18px] w-[18px]" />
              大约 10 分钟，随时可以停
            </p>
            <Link
              href={`/student/tasks/${task.id}`}
              className="patient-primary-button min-h-12 min-w-[106px] px-5"
            >
              {current > 0 ? '继续' : '开始'}
            </Link>
          </div>
        </div>
      </article>
    );
  };

  const renderCompletedTask = (task: CareTask) => (
    <Link
      key={task.id}
      href={`/student/tasks/${task.id}`}
      className="flex min-h-16 items-center gap-3 border-b-2 border-dashed border-[#eadfd0] px-4 last:border-b-0"
    >
      <ClayIcon name="check" tone="peach" size={32} className="shrink-0" />
      <span className="min-w-0 flex-1 truncate text-[16px] font-bold">
        和小晴的聊天
      </span>
      <span className="text-sm font-semibold text-[#8b8378]">
        {task.taskStatus === 'pending_review' ? '待复核' : '已完成'}
      </span>
      <span aria-hidden="true" className="text-2xl font-black leading-none text-[#b9ac9c]">
        ›
      </span>
    </Link>
  );

  return (
    <PatientLayout showNavigation>
      <div className="px-[18px] pb-4 pt-7">
        <div className="relative">
          <h1 className="text-[29px] font-black text-foreground">今天的小晴任务</h1>
          <span className="patient-sticker-tag absolute -right-1 -top-2">没有对错题</span>
        </div>

        <section className="patient-card mt-8 flex items-center gap-4 px-4 py-4">
          <ClayIcon name="leaf" tone="lemon" size={54} className="shrink-0" />
          <p className="text-lg font-black">
            今天还有
            <span className="mx-2 text-[32px] text-primary">
              {taskGroups.unfinished.length}
            </span>
            份聊天等着完成
          </p>
        </section>

        {loadError && (
          <div
            role="alert"
            className="mt-4 rounded-2xl border-2 border-[#ef6a63] bg-[#ffefee] p-3 text-sm font-semibold text-[#a24c46]"
          >
            {loadError}
          </div>
        )}

        {tasks.length === 0 ? (
          <PatientState
            kind={loadError ? 'voice-error' : 'empty-tasks'}
            title={loadError ? '任务加载失败了' : '现在没有要完成的任务'}
            description={
              loadError
                ? '检查一下网络再试试；还不行就找你的心理老师。'
                : '老师准备好了就会出现，出现前先休息一下。'
            }
            className="mt-5"
          />
        ) : (
          <div className="mt-5 space-y-7">
            {taskGroups.unfinished.length > 0 && (
              <section aria-labelledby="active-task-heading">
                <h2
                  id="active-task-heading"
                  className="mb-3 text-[18px] font-black text-foreground"
                >
                  继续完成
                </h2>
                <div className="space-y-4">
                  {taskGroups.unfinished.map(renderActiveTask)}
                </div>
              </section>
            )}

            {taskGroups.completed.length > 0 && (
              <section aria-labelledby="completed-task-heading">
                <h2
                  id="completed-task-heading"
                  className="mb-3 text-[18px] font-black text-foreground"
                >
                  已经完成
                </h2>
                <div className="patient-card-sticker overflow-hidden">
                  {taskGroups.completed.map(renderCompletedTask)}
                </div>
              </section>
            )}

            {taskGroups.cancelled.length > 0 && (
              <section aria-labelledby="cancelled-task-heading">
                <h2
                  id="cancelled-task-heading"
                  className="mb-3 text-[18px] font-black text-foreground"
                >
                  已取消
                </h2>
                <div className="patient-card overflow-hidden opacity-70">
                  {taskGroups.cancelled.map(renderCompletedTask)}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </PatientLayout>
  );
}
