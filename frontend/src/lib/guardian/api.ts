/**
 * 家长端（监护人）接口封装。
 * 作用：手机号 + 验证码登录、读取安全提醒、签署知情同意。
 */

import { apiRequest } from '@/lib/api/httpClient';

export interface GuardianProfile {
  name: string;
  relation: string;
  phone_masked: string;
}

export interface GuardianStudent {
  id: number;
  patient_no: string;
  name: string;
  sex: string;
  birthday: string | null;
}

export interface GuardianNotice {
  id: number;
  session_no: string;
  title: string;
  reason_summary: string;
  priority: string;
  occurred_at: string;
  handled: boolean;
  action_label: string;
}

export interface GuardianReferral {
  id: number;
  risk_id: number;
  referral_no: string;
  target_type: string;
  target_name: string;
  contact: string;
  suggestion: string;
  status: 'pending' | 'acknowledged' | 'completed';
  guardian_feedback: string;
  acknowledged_time: string | null;
  completed_time: string | null;
  create_time: string | null;
}

export interface GuardianPortal {
  guardian: GuardianProfile;
  student: GuardianStudent;
  encounter: { department: string; status: string } | null;
  notices: GuardianNotice[];
  report?: GuardianReportSummary | null;
  referrals?: GuardianReferral[];
}

export interface GuardianReportSummary {
  report_no: string;
  overall_risk_label: string;
  suggestions: string;
  reviewed_by: string;
  reviewed_at: string | null;
}

export interface GuardianConsentClause {
  clauseCode: string;
  clauseName: string;
  guardianContent: string;
  importanceLevel: 'important' | 'critical';
  confirmed: boolean;
}

export const guardianClauses: GuardianConsentClause[] = [
  {
    clauseCode: 'ASSESSMENT_SCOPE',
    clauseName: '心理评估知情说明',
    guardianContent:
      '本次对话为心理状态了解与筛查采集。AI 不作诊断；结论由学校心理老师复核与人工判断。',
    importanceLevel: 'important',
    confirmed: false,
  },
  {
    clauseCode: 'CONTACT_REASON',
    clauseName: '联系监护人（本通知）',
    guardianContent:
      '当出现需要监护人知晓的风险或支持需求时，学校会联系你并说明原因与范围。',
    importanceLevel: 'critical',
    confirmed: false,
  },
  {
    clauseCode: 'DATA_SCOPE',
    clauseName: '数据使用范围',
    guardianContent:
      '评估信息用于心理评估、风险识别与必要的支持安排，不用于无关用途；孩子与小晴的日常对话原文不会被转发。',
    importanceLevel: 'important',
    confirmed: false,
  },
  {
    clauseCode: 'REFERRAL_SCOPE',
    clauseName: '转介知情同意',
    guardianContent:
      '如需转介至校内或校外专业支持，会事先说明对象、目的与范围。',
    importanceLevel: 'important',
    confirmed: false,
  },
];

export async function sendGuardianCode(phone: string): Promise<{ demo_code?: string }> {
  return apiRequest<{ demo_code?: string }>('/api/guardian/send-code', {
    method: 'POST',
    body: { phone },
  });
}

export async function loginGuardian(
  phone: string,
  code: string
): Promise<GuardianPortal> {
  return apiRequest<GuardianPortal>('/api/guardian/login', {
    method: 'POST',
    body: { phone, code },
  });
}

export async function fetchGuardianPortal(): Promise<GuardianPortal> {
  return apiRequest<GuardianPortal>('/api/guardian/me');
}

export async function signGuardianConsent(input: {
  signerName: string;
  relation: string;
  clauses: GuardianConsentClause[];
  note?: string;
}): Promise<{ signed: boolean; signed_at: string }> {
  return apiRequest<{ signed: boolean; signed_at: string }>(
    '/api/guardian/consent-sign',
    {
      method: 'POST',
      body: {
        signer_name: input.signerName,
        relation: input.relation,
        clauses: input.clauses,
        note: input.note ?? '',
      },
    }
  );
}

export async function logoutGuardian(): Promise<void> {
  await apiRequest('/api/guardian/logout', { method: 'POST' });
}

/** 家长确认知悉转介单（可附反馈留言）。 */
export async function acknowledgeReferral(
  referralId: number,
  feedback: string
): Promise<GuardianReferral> {
  return apiRequest<GuardianReferral>(
    `/api/guardian/referrals/${referralId}/acknowledge`,
    {
      method: 'POST',
      body: { feedback },
    }
  );
}
