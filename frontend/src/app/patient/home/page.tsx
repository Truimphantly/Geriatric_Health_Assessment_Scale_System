'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import PatientLayout from '@/components/layout/PatientLayout';
import { NurseCallButton } from '@/components/patient/NurseCallButton';
import {
  PatientBrandMark,
  PatientIcon,
} from '@/components/patient/PatientIcon';
import { useTaskStore } from '@/lib/stores/useTaskStore';
import { useUserStore } from '@/lib/stores/useUserStore';
import { careRepository } from '@/lib/repositories';
import { runtimeConfig } from '@/lib/runtime/config';
import type { PatientNotification } from '@/lib/repositories/types';

export default function PatientHomePage() {
  const user = useUserStore((state) => state.user);
  const tasks = useTaskStore((state) => state.tasks);
  const patientTasks = tasks.filter((task) => task.patientId === user?.id);
  const [notifications, setNotifications] = useState<PatientNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const activeTask =
    patientTasks.find(
      (task) =>
        task.taskStatus === 'in_progress' || task.taskStatus === 'pending'
    ) ?? patientTasks[0];
  const current = activeTask?.progress?.current ?? 0;
  const total = activeTask?.progress?.total ?? 1;
  const progress = Math.round((current / Math.max(total, 1)) * 100);
  const taskAction =
    activeTask?.taskStatus === 'completed' ||
    activeTask?.taskStatus === 'pending_review'
      ? '查看记录'
      : current > 0
        ? '继续和小晴聊'
        : '开始和小晴聊';

  useEffect(() => {
    if (runtimeConfig.dataMode !== 'api' || !user) return;
    void careRepository
      .listPatientNotifications(true)
      .then((result) => setUnreadCount(result.unreadCount))
      .catch(() => undefined);
  }, [user]);

  const openNotifications = async () => {
    setNotificationsOpen((current) => !current);
    if (runtimeConfig.dataMode !== 'api') return;
    try {
      const result = await careRepository.listPatientNotifications(false);
      setNotifications(result.items);
      setUnreadCount(result.unreadCount);
    } catch {
      setNotifications([]);
    }
  };

  const markNotificationRead = async (notification: PatientNotification) => {
    if (!notification.readAt && runtimeConfig.dataMode === 'api') {
      try {
        await careRepository.markPatientNotificationRead(notification.id);
        setNotifications((current) =>
          current.map((item) =>
            item.id === notification.id
              ? { ...item, readAt: new Date().toISOString() }
              : item
          )
        );
        setUnreadCount((current) => Math.max(0, current - 1));
      } catch {
        // 保留通知面板，避免一次网络失败阻断学生查看其他通知。
      }
    }
  };

  return (
    <PatientLayout showNavigation>
      <div className="px-[18px] pb-4 pt-7">
        <header className="relative flex items-center justify-between">
          <h1 className="text-[29px] font-black text-foreground">心晴伙伴</h1>
          <button
            type="button"
            className="patient-touch-button relative text-foreground"
            aria-label="查看通知"
            aria-expanded={notificationsOpen}
            onClick={() => void openNotifications()}
          >
            <PatientIcon name="bell" />
            {((runtimeConfig.dataMode === 'api' && unreadCount > 0) ||
              (runtimeConfig.dataMode !== 'api' &&
                activeTask &&
                activeTask.taskStatus !== 'completed')) && (
              <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white">
                {runtimeConfig.dataMode === 'api' ? unreadCount : 1}
              </span>
            )}
          </button>
          {notificationsOpen && runtimeConfig.dataMode === 'api' && (
            <div className="absolute right-[18px] top-[72px] z-30 w-[calc(100%-36px)] max-w-[394px] rounded-2xl border border-[#f0d6c3] bg-white p-3 text-left shadow-lg">
              <p className="px-1 text-sm font-black">通知</p>
              {notifications.length ? (
                <div className="mt-2 max-h-56 space-y-2 overflow-y-auto">
                  {notifications.map((notification) => (
                    <button
                      key={notification.id}
                      type="button"
                      onClick={() => void markNotificationRead(notification)}
                      className={`w-full rounded-xl border px-3 py-2 text-left ${
                        notification.readAt
                          ? 'border-border bg-white'
                          : 'border-[#f6c8b0] bg-[#fff7f1]'
                      }`}
                    >
                      <span className="flex items-center justify-between gap-2 text-sm font-bold">
                        {notification.title}
                        {!notification.readAt && (
                          <span className="h-2 w-2 rounded-full bg-primary" />
                        )}
                      </span>
                      <span className="mt-1 block text-xs leading-5 text-foreground-muted">
                        {notification.content}
                      </span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="mt-2 px-1 text-xs text-foreground-muted">
                  暂无新通知
                </p>
              )}
            </div>
          )}
        </header>

        <section className="mt-4 flex items-center gap-3">
          <PatientBrandMark />
          <h2 className="text-[25px] font-black">
            你好，{user?.name ?? '同学'}
          </h2>
        </section>

        <section className="patient-card mt-4 flex items-center gap-3 overflow-hidden px-4 py-3">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl border-[2.5px] border-[var(--ink)] bg-[var(--accent-sky)] text-[26px]">
            🏫
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[17px] font-bold">
              {activeTask?.department ?? user?.department ?? '心理护航中心'}
              {activeTask?.bedNo ? ` · ${activeTask.bedNo}` : ''}
            </p>
            <p className="mt-0.5 text-xs text-foreground-muted">
              小晴和心理老师会一直在你身边
            </p>
          </div>
          <PatientIcon name="location" className="text-[#625954]" />
        </section>

        {activeTask ? (
          <section className="patient-card-soft mt-4 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-[22px] font-black">
                    和小晴聊聊近况
                  </h2>
                  <span className="rounded-full bg-[#ffe0cd] px-2.5 py-1 text-xs font-bold text-primary">
                    {activeTask.taskStatus === 'pending_review'
                      ? '待老师复核'
                      : activeTask.taskStatus === 'completed'
                        ? '已完成'
                        : '进行中'}
                  </span>
                </div>
                <p className="mt-1 text-[42px] font-black leading-none text-primary">
                  {progress}
                  <span className="ml-0.5 text-2xl">%</span>
                </p>
              </div>
              <div
                className="relative grid h-[82px] w-[82px] place-items-center rounded-full"
                style={{
                  background: `conic-gradient(#7fdbb6 ${progress}%, #f5e9d8 ${progress}% 100%)`,
                }}
                aria-label={`任务完成进度 ${progress}%`}
              >
                <span className="grid h-[62px] w-[62px] place-items-center rounded-full border-2 border-[var(--ink)] bg-[#fffaf4] text-[26px]">
                  💬
                </span>
              </div>
            </div>
            <div className="patient-progress-track mt-3">
              <div
                className="patient-progress-value"
                style={{ width: `${progress}%` }}
              />
            </div>
            <Link
              href={`/patient/tasks/${activeTask.id}`}
              className="patient-primary-button mt-3 w-full"
            >
              {taskAction}
            </Link>
          </section>
        ) : (
          <section className="patient-card mt-4 p-5 text-center">
            <span className="mx-auto grid h-[72px] w-[72px] place-items-center rounded-3xl border-[2.5px] border-[var(--ink)] bg-[var(--accent-mint)] text-[34px]">
              🌱
            </span>
            <h2 className="mt-3 text-lg font-black">现在没有要完成的任务</h2>
            <p className="mt-1 text-sm text-foreground-muted">
              老师准备好了就会出现
            </p>
          </section>
        )}

        <section className="patient-card-sticker mt-4 flex min-h-[96px] items-center gap-3 px-4">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl border-[2.5px] border-[var(--ink)] bg-[var(--accent-peach)] text-[26px]">
            🫂
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-lg font-black text-foreground">需要人陪？</p>
            <p className="text-sm font-bold text-foreground-muted">叫心理老师来聊聊</p>
          </div>
          <NurseCallButton
            taskId={activeTask?.id}
            className="h-14 w-14 shrink-0 rounded-full p-0 [&_svg]:h-7 [&_svg]:w-7"
            compact
            iconOnly
          />
        </section>

        <section className="mt-4 grid grid-cols-3 gap-3">
          {[
            {
              href: '/patient/tasks',
              title: '我的任务',
              icon: 'clipboard' as const,
              tone: 'bg-[var(--accent-lemon)] text-foreground',
            },
            {
              href: '/patient/assistant',
              title: '小晴助手',
              icon: 'nav-assistant' as const,
              tone: 'bg-[var(--accent-mint)] text-foreground',
            },
            {
              href: '/patient/assistant',
              title: '求助资源',
              icon: 'document' as const,
              tone: 'bg-[var(--accent-sky)] text-foreground',
            },
          ].map((item) => (
            <Link
              key={item.title}
              href={item.href}
              className={`flex min-h-[110px] flex-col items-center justify-center gap-2 rounded-[20px] border-[2.5px] border-[var(--ink)] ${item.tone} shadow-[3px_3px_0_var(--ink)]`}
            >
              <PatientIcon name={item.icon} className="h-9 w-9" />
              <span className="text-sm font-black text-foreground">
                {item.title}
              </span>
            </Link>
          ))}
        </section>
      </div>
    </PatientLayout>
  );
}
