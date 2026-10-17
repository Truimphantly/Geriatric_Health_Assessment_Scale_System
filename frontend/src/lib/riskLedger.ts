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
