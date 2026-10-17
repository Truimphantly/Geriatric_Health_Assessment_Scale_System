'use client';

import Image from 'next/image';
import { PatientIcon } from '@/components/patient/PatientIcon';
import { runtimeConfig } from '@/lib/runtime/config';
import type { InteractionMessage } from '@/lib/types';

export function PatientChatBubble({
  message,
}: {
  message: InteractionMessage;
}) {
  const isPatient = message.role === 'patient';
  const audioSrc = message.audioUrl
    ? new URL(message.audioUrl, runtimeConfig.apiBaseUrl).toString()
    : undefined;

  return (
    <div
      className={`mb-5 flex items-start gap-2.5 ${
        isPatient ? 'flex-row-reverse' : ''
      }`}
    >
      {isPatient ? (
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--accent-peach)] text-[#5a4038] shadow-[inset_0_2px_0_rgb(255_255_255_/_65%),0_6px_12px_rgb(94_78_55_/_0.14)]">
          <PatientIcon name="user" className="h-5 w-5" />
        </span>
      ) : (
        <Image
          src="/assets/patient/illustrations/assistant-avatar.webp"
          alt="小晴"
          width={40}
          height={40}
          className="h-10 w-10 shrink-0 rounded-full bg-[#fdf6e8] object-contain shadow-[inset_0_2px_0_#fff,0_6px_14px_rgb(94_78_55_/_0.14)]"
        />
      )}

      <div className={`max-w-[82%] ${isPatient ? 'text-right' : ''}`}>
        <p
          className={`mb-1 px-1 text-xs font-black ${
            isPatient ? 'text-primary' : 'text-[#a08a6b]'
          }`}
        >
          {isPatient ? '我' : '小晴'}
        </p>
        <div
          className={`rounded-[22px] px-4 py-3 text-left text-[15px] leading-7 ${
            isPatient
              ? 'rounded-tr-md bg-gradient-to-br from-[#a9e4cb] to-[#7ccfae] text-[#234234] shadow-[inset_0_2px_0_rgb(255_255_255_/_55%),0_10px_20px_rgb(96_165_132_/_22%)]'
              : 'rounded-tl-md bg-[#fffdf9] text-foreground shadow-[inset_0_2px_0_#fff,0_10px_22px_rgb(94_78_55_/_0.12),0_26px_40px_rgb(94_78_55_/_0.06)]'
          }`}
        >
          {message.contentText && (
            <p className="whitespace-pre-wrap">{message.contentText}</p>
          )}
          {audioSrc && (
            <div
              className={`mt-2 border-t pt-2 ${
                isPatient ? 'border-white/35' : 'border-[#efe4d3]'
              }`}
            >
              <audio
                controls
                preload="metadata"
                src={audioSrc}
                crossOrigin="use-credentials"
                className="h-8 min-w-0 max-w-full"
              />
            </div>
          )}
          {message.isStreaming && (
            <span className="mt-1 inline-flex items-center gap-1 text-xs opacity-70">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
              正在回复
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
