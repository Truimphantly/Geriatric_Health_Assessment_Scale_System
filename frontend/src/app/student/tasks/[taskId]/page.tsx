'use client';

import { useParams, useRouter } from 'next/navigation';
import PatientLayout from '@/components/layout/PatientLayout';
import { PatientState } from '@/components/patient/PatientState';
import { isPatientTaskReadOnly } from '@/lib/patient/taskGroups';
import { ClayIcon } from '@/components/patient/ClayIcon';
import { useTaskStore } from '@/lib/stores/useTaskStore';

/**
 * 学生端任务详情：只呈现"接下来会发生什么"，
 * 不展示量表名称、筛查主题等专业信息（避免标签化与抵触）。
 */
export default function PatientTaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const router = useRouter();
  const task = useTaskStore((state) =>
    state.tasks.find((item) => item.id === taskId)
  );

  if (!task) {
    return (
      <PatientLayout title="任务详情" showBack>
        <div className="p-[18px]">
          <PatientState
            kind="empty-tasks"
            title="任务不存在或已经失效"
            description="请返回任务中心查看最新任务。"
          />
          <button
            className="patient-primary-button mt-4 w-full"
            onClick={() => router.push('/student/tasks')}
          >
            返回任务中心
          </button>
        </div>
      </PatientLayout>
    );
  }

  const startPath =
    task.collectionMode === 'ai_dialogue'
      ? `/student/dialogue/${task.id}`
      : `/student/form/${task.id}`;
  const canViewDialogue =
    task.collectionMode === 'ai_dialogue' && isPatientTaskReadOnly(task);
  const finished =
    task.taskStatus === 'pending_review' || task.taskStatus === 'completed';

  return (
    <PatientLayout
      title="和小晴聊聊"
      showBack
      onBack={() => router.push('/student/tasks')}
    >
      <div className="space-y-4 px-[18px] pb-8 pt-4">
        <section className="patient-card p-5">
          <div className="flex items-center gap-4">
            <span className="patient-sticker-tag shrink-0">今天</span>
            <div className="min-w-0 flex-1">
              <h1 className="text-[26px] font-black leading-snug">
                和小晴聊一聊近况
              </h1>
              <p className="mt-1 text-sm font-semibold text-foreground-muted">
                像跟朋友聊天一样，大约 10 分钟
              </p>
            </div>
            <ClayIcon name="chat" tone="lemon" size={54} className="shrink-0" />
          </div>

          <div className="mt-5 space-y-3">
            {[
              {
                icon: 'moon' as const,
                title: '小晴会先聊些轻松的话题',
                detail: '比如最近的睡眠、心情、和同学朋友的小事，没有标准答案',
              },
              {
                icon: 'edit' as const,
                title: '说错了随时改，不想说就跳过',
                detail: '语音、打字都可以；随时暂停，下次接着聊',
              },
              {
                icon: 'mail' as const,
                title: '聊完你可以选择怎么处理这份记录',
                detail: '需要时，小晴会帮你把求助信息递给心理老师',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-3 rounded-2xl bg-surface-secondary p-3.5 shadow-[inset_0_2px_0_#fff,0_8px_16px_rgb(94_78_55_/_0.10)]"
              >
                <ClayIcon name={item.icon} tone="sky" size={36} className="shrink-0" />
                <div className="min-w-0">
                  <p className="text-[15px] font-black">{item.title}</p>
                  <p className="mt-0.5 text-xs leading-5 text-foreground-muted">
                    {item.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {finished && (
            <p className="mt-4 rounded-2xl bg-[var(--accent-sky)] p-3 text-sm font-bold shadow-[inset_0_2px_0_rgb(255_255_255_/_65%),0_8px_16px_rgb(94_78_55_/_0.10)]">
              这次的聊天已经完成啦，记录已交给心理老师查看。
            </p>
          )}
        </section>

        {task.taskStatus === 'pending_review' ? (
          <section className="patient-card-sticker p-5 text-center">
            <p className="text-[34px]">📮</p>
            <p className="mt-2 text-lg font-black">记录已交给心理老师</p>
            <p className="mt-1 text-sm font-semibold text-foreground-muted">
              老师会看完再决定怎么更好地支持你
            </p>
            {canViewDialogue && (
              <button
                className="patient-outline-button mt-4 w-full"
                onClick={() => router.push(`/student/dialogue/${task.id}`)}
              >
                回看这次聊天
              </button>
            )}
          </section>
        ) : task.taskStatus === 'completed' ? (
          <div className="space-y-3">
            <button
              className="patient-primary-button w-full"
              onClick={() => router.push(`/student/complete/${task.id}`)}
            >
              查看完成情况
            </button>
            {canViewDialogue && (
              <button
                className="patient-outline-button w-full"
                onClick={() => router.push(`/student/dialogue/${task.id}`)}
              >
                回看这次聊天
              </button>
            )}
          </div>
        ) : (
          <button
            className="patient-primary-button w-full"
            onClick={() => router.push(startPath)}
          >
            {task.taskStatus === 'in_progress' ? '从上次位置继续聊 →' : '开始聊天 →'}
          </button>
        )}

        <p className="px-2 text-center text-xs font-semibold leading-5 text-foreground-muted">
          聊天内容严格保密，只有涉及安全时小晴才会告诉心理老师来帮你。
        </p>
      </div>
    </PatientLayout>
  );
}
