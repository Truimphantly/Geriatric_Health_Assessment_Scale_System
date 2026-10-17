'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { NurseCallButton } from '@/components/patient/NurseCallButton';
import PatientLayout from '@/components/layout/PatientLayout';
import { PatientIcon } from '@/components/patient/PatientIcon';
import { useTaskStore } from '@/lib/stores/useTaskStore';
import { useUserStore } from '@/lib/stores/useUserStore';
import { careRepository } from '@/lib/repositories';
import { runtimeConfig } from '@/lib/runtime/config';
import { createClientInvocationId } from '@/lib/clientInvocation';
import type { PatientAssistantSession } from '@/lib/repositories/types';

interface AssistantMessage {
  id: string | number;
  role: 'assistant' | 'patient';
  content: string;
}

const answers: Record<string, string> = {
  热线: '心理援助热线 12356 与青少年服务台 12355 全天有人值守，随时可以打。',
  求助: '想找心理老师聊聊天，可以在对话里说“帮我联系心理老师”，小晴会帮你递请求。',
  保密: '和小晴的聊天内容严格保密，只有遇到危险情况会通知心理老师来帮忙。',
  求助方式: '床头和卫生间均设有求助方式。身体不适、输液异常或需要下床协助时请及时使用。',
};

const quickQuestions = ['睡不着怎么办？', '怎么找心理老师？', '压力大怎么放松？'];

export default function PatientAssistantPage() {
  const [input, setInput] = useState('');
  const [voiceHint, setVoiceHint] = useState(false);
  const [assistantSession, setAssistantSession] =
    useState<PatientAssistantSession>();
  const [configuredQuestions, setConfiguredQuestions] =
    useState(runtimeConfig.dataMode === 'api' ? [] : quickQuestions);
  const user = useUserStore((state) => state.user);
  const task = useTaskStore((state) =>
    state.tasks.find(
      (item) =>
        item.patientId === user?.id &&
        item.taskStatus !== 'completed' &&
        item.taskStatus !== 'cancelled'
    )
  );
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: 1,
      role: 'assistant',
      content:
        '你好呀！我是小晴，想聊聊最近的睡眠、压力、还是和同学朋友的事？',
    },
  ]);

  useEffect(() => {
    if (runtimeConfig.dataMode !== 'api') return;
    let cancelled = false;
    void (async () => {
      try {
        const [session, guides] = await Promise.all([
          careRepository.createPatientAssistantSession('text'),
          careRepository.listPatientWardGuide(),
        ]);
        if (cancelled) return;
        setAssistantSession(session);
        if (guides.length) {
          setConfiguredQuestions(guides.slice(0, 3).map((guide) => guide.title));
        }
        const history = session.messages
          .filter((item) => item.role !== 'system')
          .map((item) => ({
            id: item.messageNo,
            role:
              item.role === 'patient'
                ? ('patient' as const)
                : ('assistant' as const),
            content: item.content,
          }));
        if (history.length) setMessages(history);
      } catch {
        if (!cancelled) {
          setConfiguredQuestions([]);
          setMessages([
            {
              id: 'assistant-unavailable',
              role: 'assistant',
              content:
                '帮助小知识暂时没加载出来，可以直接跟我说说你的困扰；超出能力范围的问题我会建议你找心理老师。',
            },
          ]);
          setVoiceHint(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const send = async (content: string) => {
    const text = content.trim();
    if (!text) return;
    if (runtimeConfig.dataMode === 'api') {
      if (!assistantSession) {
        setVoiceHint(true);
        return;
      }
      try {
        const next = await careRepository.sendPatientAssistantMessage(
          assistantSession.sessionNo,
          text,
          createClientInvocationId('assistant-message')
        );
        setAssistantSession(next);
        setMessages(
          next.messages
            .filter((item) => item.role !== 'system')
            .map((item) => ({
              id: item.messageNo,
              role:
                item.role === 'patient'
                  ? ('patient' as const)
                  : ('assistant' as const),
              content: item.content,
            }))
        );
      } catch {
        setVoiceHint(true);
      }
      setInput('');
      return;
    }
    const matched = Object.entries(answers).find(([keyword]) =>
      text.includes(keyword)
    );
    const response = matched
      ? matched[1]
      : '这个问题可能涉及专业判断，我不能直接回答。可以找心理老师聊聊——需要的话我帮你呼叫，也可以在对话里直接说。';
    setMessages((current) => [
      ...current,
      { id: Date.now(), role: 'patient', content: text },
      { id: Date.now() + 1, role: 'assistant', content: response },
    ]);
    setInput('');
    setVoiceHint(false);
  };

  return (
    <PatientLayout showNavigation>
      <div className="flex min-h-[calc(100dvh-92px)] flex-col px-[18px] pb-3 pt-7">
        <header className="text-center">
          <h1 className="text-[30px] font-black text-[#4a241c]">小晴助手</h1>
          <div className="mt-4 flex min-h-12 items-center justify-center gap-2 rounded-2xl border border-[#f1c9a7] bg-[#fffaf4] px-3 text-[13px] font-bold text-primary">
            <PatientIcon name="shield" className="h-5 w-5" />
            陪你聊聊天，不诊断、不给标签
          </div>
        </header>

        <section
          className="scrollbar-soft mt-5 flex-1 space-y-4 overflow-y-auto pb-4"
          aria-label="小晴助手对话"
        >
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-3 ${
                message.role === 'patient' ? 'flex-row-reverse' : ''
              }`}
            >
              {message.role === 'assistant' ? (
                <Image
                  src="/xiaoqing/xq-01-default.png"
                  alt="小晴助手"
                  width={58}
                  height={58}
                  className="h-14 w-14 shrink-0 object-contain drop-shadow-[0_6px_14px_rgb(94_78_55/0.14)]"
                />
              ) : (
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#ffe8da] text-primary">
                  <PatientIcon name="user" className="h-5 w-5" />
                </span>
              )}
              <div className={message.role === 'assistant' ? 'max-w-[78%]' : 'max-w-[82%]'}>
                <p
                  className={`mb-1 text-sm font-bold ${
                    message.role === 'assistant'
                      ? 'text-foreground'
                      : 'text-right text-primary'
                  }`}
                >
                  {message.role === 'assistant'
                    ? '小晴助手'
                    : user?.name ?? '我'}
                </p>
                <div
                  className={`rounded-[20px] px-4 py-3 text-[15px] leading-7 shadow-sm ${
                    message.role === 'assistant'
                      ? 'rounded-tl-md border border-[#eadfd6] bg-white'
                      : 'rounded-tr-md bg-gradient-to-br from-[#ff7557] to-[#ff5335] text-white'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            </div>
          ))}

          {messages.length === 1 && (
            <div className="patient-card ml-[68px] p-3">
              <p className="mb-2 text-sm text-foreground-muted">您可以问我：</p>
              <div className="space-y-2">
                {configuredQuestions.map((question, index) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => void send(question)}
                    className="flex min-h-[52px] w-full items-center gap-3 rounded-2xl border border-[#f0d1ba] bg-[#fffaf5] px-3 text-left text-[15px] font-bold"
                  >
                    <span className="grid h-8 w-8 place-items-center rounded-full bg-[#ffe8da] text-primary">
                      <PatientIcon
                        name={
                          index === 0
                            ? 'hospital'
                            : index === 1
                              ? 'nurse'
                              : 'family'
                        }
                        className="h-[18px] w-[18px]"
                      />
                    </span>
                    <span className="flex-1">{question}</span>
                    <span
                      aria-hidden="true"
                      className="text-2xl leading-none text-foreground-muted"
                    >
                      ›
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </section>

        {voiceHint && (
          <div
            role="status"
            className="mb-2 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800"
          >
            小晴助手的语音问答还没开放；先用文字聊也可以，评估对话里的语音功能不受影响。
          </div>
        )}

        <div className="patient-card flex items-center gap-2 p-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="想聊点什么？"
            className="min-h-12 min-w-0 flex-1 rounded-full border border-[#efcdb5] bg-[#fffdfb] px-4 text-[15px] outline-none focus:border-primary"
            onKeyDown={(event) => {
                if (event.key === 'Enter') void send(input);
            }}
          />
          {input.trim() ? (
            <button
              type="button"
              onClick={() => void send(input)}
              className="patient-touch-button bg-primary text-white"
              aria-label="发送"
            >
              <PatientIcon name="send" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setVoiceHint((current) => !current)}
              className="patient-touch-button bg-primary text-white"
              aria-label="语音输入"
              aria-pressed={voiceHint}
            >
              <PatientIcon name="microphone" />
            </button>
          )}
        </div>

        <NurseCallButton
          taskId={task?.id}
          reason="学生在小晴助手页面主动呼叫心理老师"
          className="mt-3 w-full"
        />
      </div>
    </PatientLayout>
  );
}
