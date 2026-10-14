'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import PatientLayout from '@/components/layout/PatientLayout';
import { PatientIcon } from '@/components/patient/PatientIcon';
import { careRepository } from '@/lib/repositories';
import { runtimeConfig } from '@/lib/runtime/config';
import { useTaskStore } from '@/lib/stores/useTaskStore';
import { useUserStore } from '@/lib/stores/useUserStore';
import { mockPatients } from '@/lib/mock/data';

export default function PatientVerifyPage() {
  return (
    <Suspense fallback={<VerifyFallback />}>
      <PatientVerifyContent />
    </Suspense>
  );
}

function VerifyFallback() {
  return (
    <PatientLayout>
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="text-center">
          {/* 小晴头像：占位 SVG，后续替换官方卡通形象素材 */}
          <XiaoQingFace size={80} />
          <p className="mt-4 font-medium text-foreground-muted">
            正在打开小晴的门…
          </p>
        </div>
      </div>
    </PatientLayout>
  );
}

/** 小晴头像（贴纸风占位 SVG，金色圆头机器人 + 腮红 + 天线） */
function XiaoQingFace({ size = 96 }: { size?: number }) {
  return (
    <svg viewBox="0 0 200 200" width={size} height={size} aria-label="小晴" role="img">
      <circle cx="100" cy="100" r="96" fill="#FFF9F2" stroke="#2A2320" strokeWidth="4" />
      <g>
        <circle cx="70" cy="90" r="9" fill="#2A2320" />
        <circle cx="130" cy="90" r="9" fill="#2A2320" />
        <circle cx="73" cy="86" r="3" fill="#FFF9F2" />
        <circle cx="133" cy="86" r="3" fill="#FFF9F2" />
      </g>
      <ellipse cx="52" cy="114" rx="10" ry="6.5" fill="#FFB5A7" />
      <ellipse cx="148" cy="114" rx="10" ry="6.5" fill="#FFB5A7" />
      <path d="M84 110 q16 13 32 2" fill="none" stroke="#2A2320" strokeWidth="4" strokeLinecap="round" />
      <circle cx="100" cy="34" r="9" fill="#7FDBB6" stroke="#2A2320" strokeWidth="3" />
      <line x1="100" y1="43" x2="100" y2="56" stroke="#2A2320" strokeWidth="3" />
    </svg>
  );
}

function PatientVerifyContent() {
  const apiMode = runtimeConfig.dataMode === 'api';
  const router = useRouter();
  const searchParams = useSearchParams();
  const { tasks, setTasks, updateTask } = useTaskStore();
  const { login } = useUserStore();
  const [taskNo, setTaskNo] = useState(() => searchParams.get('taskNo') ?? '');
  const [idCardNo, setIdCardNo] = useState('');
  const [participantType, setParticipantType] = useState<'patient' | 'family'>('patient');
  const [relationship, setRelationship] = useState('女儿');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [scanToken, setScanToken] = useState('');
  const [scanOpen, setScanOpen] = useState(false);

  const fillDemo = (mode: 'ai' | 'form') => {
    const task = tasks.find((item) =>
      mode === 'ai'
        ? item.collectionMode === 'ai_dialogue'
        : item.collectionMode === 'traditional_form'
    );
    if (!task) return;
    const patient = mockPatients.find((item) => item.id === task.patientId);
    setTaskNo(task.taskNo);
    setIdCardNo(patient?.idCard ?? '');
    setError('');
  };

  const handleVerify = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    if (apiMode) {
      try {
        // 主流程：任务号 + 证件后四位（verify-task），与心理老师下发任务一一对应
        const portal = await careRepository.verifyPatientTask({
          taskNo: taskNo.trim(),
          idCardSuffix: idCardNo.trim(),
        });
        setTasks(portal.tasks);
        login({
          id: portal.patient.id,
          role: 'patient',
          name: portal.patient.name,
          department: portal.encounter.department,
        });
        router.push('/patient/tasks');
      } catch (loginError) {
        setError(
          loginError instanceof Error ? loginError.message : '患者身份核验失败'
        );
      } finally {
        setLoading(false);
      }
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 450));

    const task = tasks.find((item) => item.taskNo.toLowerCase() === taskNo.trim().toLowerCase());
    const patient = task
      ? mockPatients.find((item) => item.id === task.patientId)
      : undefined;

    if (!task || !patient) {
      setError('没有找到该任务，请检查任务编号');
      setLoading(false);
      return;
    }

    if (patient.idCard !== idCardNo.trim()) {
      setError('证件后四位与任务患者不匹配');
      setLoading(false);
      return;
    }

    updateTask(task.id, {
      participantType,
      participantName: participantType === 'patient' ? patient.name : `${patient.name}家属`,
      relationshipToPatient: participantType === 'family' ? relationship : undefined,
    });
    login({
      id: patient.id,
      role: 'patient',
      name: patient.name,
      department: task.department,
    });
    router.push('/patient/tasks');
  };

  const handleScanVerify = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!scanToken.trim()) return;
    setError('');
    setLoading(true);
    try {
      const portal = await careRepository.verifyPatientScanToken(scanToken.trim());
      setTasks(portal.tasks);
      login({
        id: portal.patient.id,
        role: 'patient',
        name: portal.patient.name,
        department: portal.encounter.department,
      });
      router.push('/patient/tasks');
    } catch (scanError) {
      setError(
        scanError instanceof Error ? scanError.message : '扫码核验失败，请重新扫码'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <PatientLayout>
      <div className="relative min-h-screen px-[18px] pb-8 pt-9">
        <div className="relative z-10 pt-1 text-center">
          <XiaoQingFace size={92} />
          <h1 className="mt-4 text-[32px] font-black leading-tight text-foreground">
            心晴伙伴
          </h1>
          <div className="mt-3 flex items-center justify-center gap-3">
            <span className="patient-sticker-tag">学生入口</span>
            <p className="text-base font-bold">和小晴聊一聊最近的状态</p>
          </div>

          <div className="patient-card mt-6 overflow-hidden p-4 text-left">
            <form onSubmit={handleVerify} className="space-y-5">
              {!apiMode && (
                <div className="grid grid-cols-2 rounded-2xl border-2 border-foreground bg-surface-secondary p-1">
                  {(
                    [
                      ['patient', '患者本人'],
                      ['family', '家属协助'],
                    ] as const
                  ).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setParticipantType(value)}
                      className={`min-h-12 rounded-xl text-[16px] font-bold transition ${
                        participantType === value
                          ? 'bg-[var(--accent-mint)] text-foreground shadow-[2px_2px_0_var(--ink)]'
                          : 'text-foreground-muted'
                      }`}
                      aria-pressed={participantType === value}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              )}

              <label className="patient-field flex items-center gap-3 px-4">
                <PatientIcon name="clipboard" className="text-foreground-muted" />
                <span className="shrink-0 text-[16px] font-black">任务号</span>
                <input
                  value={taskNo}
                  onChange={(event) => setTaskNo(event.target.value)}
                  placeholder="心理老师给你的编号"
                  className="min-w-0 flex-1 bg-transparent text-[15px] font-bold outline-none placeholder:font-medium placeholder:text-foreground-placeholder"
                  required
                />
              </label>

              <label className="patient-field flex items-center gap-3 px-4">
                <PatientIcon name="user" className="text-foreground-muted" />
                <span className="shrink-0 text-[16px] font-black">证件后四位</span>
                <input
                  value={idCardNo}
                  onChange={(event) => setIdCardNo(event.target.value)}
                  placeholder="登记证件的最后 4 位"
                  maxLength={apiMode ? 4 : 4}
                  inputMode={apiMode ? 'numeric' : 'text'}
                  pattern={apiMode ? '[0-9Xx]{4}' : undefined}
                  className="min-w-0 flex-1 bg-transparent text-[15px] font-bold outline-none placeholder:font-medium placeholder:text-foreground-placeholder"
                  required
                />
              </label>

              {!apiMode && participantType === 'family' && (
                <label className="patient-field flex items-center gap-3 px-4">
                  <PatientIcon name="family" className="text-foreground-muted" />
                  <span className="shrink-0 text-[16px] font-bold">与患者关系</span>
                  <select
                    value={relationship}
                    onChange={(event) => setRelationship(event.target.value)}
                    className="min-w-0 flex-1 bg-transparent text-right text-[15px] outline-none"
                  >
                    <option>女儿</option>
                    <option>儿子</option>
                    <option>配偶</option>
                    <option>其他家属</option>
                  </select>
                </label>
              )}

              {error && (
                <div
                  role="alert"
                  className="rounded-2xl border-2 border-[#ef6a63] bg-[#ffefee] px-4 py-3 text-left text-sm font-semibold text-[#a24c46]"
                >
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="patient-primary-button w-full justify-center"
              >
                {loading ? '正在核验…' : '进入小晴 →'}
              </button>
            </form>

            {!apiMode && (
              <>
                <div className="my-4 flex items-center gap-3">
                  <span className="h-px flex-1 bg-border" />
                  <span className="text-xs text-foreground-muted">快速体验</span>
                  <span className="h-px flex-1 bg-border" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    className="patient-outline-button min-h-11 text-sm"
                    onClick={() => fillDemo('ai')}
                  >
                    AI 对话任务
                  </button>
                  <button
                    type="button"
                    className="patient-outline-button min-h-11 text-sm"
                    onClick={() => fillDemo('form')}
                  >
                    传统问卷任务
                  </button>
                </div>
              </>
            )}

            <button
              type="button"
              className="patient-outline-button mt-3 w-full"
              onClick={() => {
                setScanOpen((current) => !current);
                setError('');
              }}
            >
              <PatientIcon name="qr" />
              {scanOpen ? '关闭扫码核验' : '扫码进入'}
            </button>

            {scanOpen && (
              <form
                onSubmit={handleScanVerify}
                className="mt-3 rounded-2xl border-2 border-foreground bg-surface-secondary p-3"
              >
                <label className="text-sm font-bold text-foreground-muted">
                  扫码后粘贴一次性令牌
                  <input
                    value={scanToken}
                    onChange={(event) => setScanToken(event.target.value)}
                    placeholder="等待二维码内容…"
                    className="patient-field mt-2 w-full px-3 text-sm outline-none"
                    minLength={24}
                    required
                  />
                </label>
                <button
                  type="submit"
                  disabled={loading}
                  className="patient-primary-button mt-3 w-full justify-center"
                >
                  {loading ? '正在核验…' : '核验扫码令牌'}
                </button>
                <p className="mt-2 text-xs leading-5 text-foreground-muted">
                  相机未开启时可粘贴二维码内容；令牌只能使用一次，过期请让心理老师重新生成。
                </p>
              </form>
            )}
          </div>

          <p className="mt-4 flex items-center justify-center gap-2 text-sm font-semibold text-foreground-muted">
            <PatientIcon name="shield" className="h-4 w-4" />
            你说的话只有你和小晴知道
          </p>

          {apiMode && (
            <div className="mt-3 rounded-2xl border-2 border-foreground bg-[var(--accent-lemon)] p-3 text-left text-xs font-semibold leading-5 text-[#4a3f10] shadow-[3px_3px_0_var(--ink)]">
              任务号和证件后四位来自心理老师的小纸条或二维码（300 秒有效）。进门后先读一遍知情同意，可慢慢读、随时退出。
            </div>
          )}
        </div>
      </div>
    </PatientLayout>
  );
}
