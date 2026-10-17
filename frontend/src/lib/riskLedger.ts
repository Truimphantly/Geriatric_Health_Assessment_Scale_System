/**
 * 风险台账数据访问。
 *
 * 作用：教师端风险档案的查询与处理（状态流转 / 等级调整 / 跟进记录）。
 *       后端 DTO 为 snake_case，这里统一映射为 camelCase 供页面使用。
 */

import { apiRequest } from '@/lib/api/httpClient';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type RiskStatus = 'open' | 'following' | 'referred' | 'closed';

export interface RiskFollowUp {
  time: string;
  by: string;
  action: string;
  note: string;
}

export interface RiskItem {
  id: number;
  studentId: number;
  studentNo: string | null;
  studentName: string;
  level: RiskLevel;
  status: RiskStatus;
  source: string;
  reason: string;
  followUps: RiskFollowUp[];
  createTime: string | null;
  updateTime: string | null;
}

export interface RiskStats {
  open: number;
  following: number;
  referred: number;
  closed: number;
  highOrAbove: number;
}

export interface RiskListData {
  items: RiskItem[];
  stats: RiskStats;
}

interface RiskItemDto {
  id: number;
  student_id: number;
  student_no: string | null;
  student_name: string;
  level: string;
  status: string;
  source: string;
  reason: string;
  follow_ups: RiskFollowUp[];
  create_time: string | null;
  update_time: string | null;
}

interface RiskStatsDto {
  open: number;
  following: number;
  referred: number;
  closed: number;
  high_or_above: number;
}

interface RiskListDto {
  items: RiskItemDto[];
  stats: RiskStatsDto;
}

function mapFollowUp(entry: RiskFollowUp): RiskFollowUp {
  return {
    time: entry.time ?? '',
    by: entry.by ?? '',
    action: entry.action ?? '',
    note: entry.note ?? '',
  };
}

function mapRiskItem(dto: RiskItemDto): RiskItem {
  return {
    id: dto.id,
    studentId: dto.student_id,
    studentNo: dto.student_no,
    studentName: dto.student_name,
    level: (dto.level ?? 'medium') as RiskLevel,
    status: (dto.status ?? 'open') as RiskStatus,
    source: dto.source ?? 'agent',
    reason: dto.reason ?? '',
    followUps: (dto.follow_ups ?? []).map(mapFollowUp),
    createTime: dto.create_time,
    updateTime: dto.update_time,
  };
}

export async function listRisks(
  filters: { status?: RiskStatus; level?: RiskLevel } = {},
  signal?: AbortSignal
): Promise<RiskListData> {
  const query = new URLSearchParams();
  if (filters.status) query.set('status', filters.status);
  if (filters.level) query.set('level', filters.level);
  const suffix = query.size ? `?${query.toString()}` : '';
  const dto = await apiRequest<RiskListDto>(`/api/risks${suffix}`, { signal });
  return {
    items: dto.items.map(mapRiskItem),
    stats: {
      open: dto.stats?.open ?? 0,
      following: dto.stats?.following ?? 0,
      referred: dto.stats?.referred ?? 0,
      closed: dto.stats?.closed ?? 0,
      highOrAbove: dto.stats?.high_or_above ?? 0,
    },
  };
}

export async function updateRisk(
  riskId: number,
  input: { status?: RiskStatus; level?: RiskLevel; note?: string },
  signal?: AbortSignal
): Promise<RiskItem> {
  const dto = await apiRequest<RiskItemDto>(`/api/risks/${riskId}/update`, {
    method: 'POST',
    body: {
      status: input.status ?? null,
      level: input.level ?? null,
      note: input.note ?? '',
    },
    signal,
  });
  return mapRiskItem(dto);
}

export const RISK_LEVEL_LABEL: Record<RiskLevel, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '极高',
};

export const RISK_STATUS_LABEL: Record<RiskStatus, string> = {
  open: '待跟进',
  following: '跟进中',
  referred: '已转介',
  closed: '已结案',
};

export const RISK_SOURCE_LABEL: Record<string, string> = {
  keyword_fallback: '关键词兜底',
  agent: 'AI 上报',
  student: '学生呼叫',
  teacher: '教师判定',
  scale_threshold: '量表阈值',
};

export const REFERRAL_TARGET_LABEL: Record<string, string> = {
  school_counseling: '校心理辅导室',
  professional_counseling: '校外专业机构',
  family_support: '家庭支持',
  other: '其他',
};

export type ReferralStatus = 'pending' | 'acknowledged' | 'completed';

export const REFERRAL_STATUS_LABEL: Record<ReferralStatus, string> = {
  pending: '待家长确认',
  acknowledged: '已确认·进行中',
  completed: '已完成',
};

export interface ReferralItem {
  id: number;
  riskId: number;
  studentId: number;
  studentName: string;
  referralNo: string;
  targetType: string;
  targetName: string;
  contact: string;
  suggestion: string;
  status: ReferralStatus;
  guardianFeedback: string;
  acknowledgedTime: string | null;
  completedTime: string | null;
  createTime: string | null;
}

interface ReferralItemDto {
  id: number;
  risk_id: number;
  student_id: number;
  student_name: string;
  referral_no: string;
  target_type: string;
  target_name: string;
  contact: string;
  suggestion: string;
  status: string;
  guardian_feedback: string;
  acknowledged_time: string | null;
  completed_time: string | null;
  create_time: string | null;
}

function mapReferral(dto: ReferralItemDto): ReferralItem {
  return {
    id: dto.id,
    riskId: dto.risk_id,
    studentId: dto.student_id,
    studentName: dto.student_name,
    referralNo: dto.referral_no,
    targetType: dto.target_type,
    targetName: dto.target_name,
    contact: dto.contact ?? '',
    suggestion: dto.suggestion ?? '',
    status: (dto.status ?? 'pending') as ReferralStatus,
    guardianFeedback: dto.guardian_feedback ?? '',
    acknowledgedTime: dto.acknowledged_time,
    completedTime: dto.completed_time,
    createTime: dto.create_time,
  };
}

export async function listRiskReferrals(
  riskId: number,
  signal?: AbortSignal
): Promise<ReferralItem[]> {
  const dto = await apiRequest<ReferralItemDto[]>(
    `/api/risks/${riskId}/referrals`,
    { signal }
  );
  return dto.map(mapReferral);
}

export async function createReferral(
  riskId: number,
  input: {
    targetType: string;
    targetName: string;
    contact?: string;
    suggestion?: string;
  },
  signal?: AbortSignal
): Promise<ReferralItem> {
  const dto = await apiRequest<ReferralItemDto>(
    `/api/risks/${riskId}/referrals`,
    {
      method: 'POST',
      body: {
        target_type: input.targetType,
        target_name: input.targetName,
        contact: input.contact ?? '',
        suggestion: input.suggestion ?? '',
      },
      signal,
    }
  );
  return mapReferral(dto);
}

export async function completeReferral(
  referralId: number,
  note = '',
  signal?: AbortSignal
): Promise<ReferralItem> {
  const dto = await apiRequest<ReferralItemDto>(
    `/api/referrals/${referralId}/complete`,
    {
      method: 'POST',
      body: { note },
      signal,
    }
  );
  return mapReferral(dto);
}
