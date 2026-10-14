export interface PatientDemoAccount {
  name: string;
  idCardNo: string;
  phone: string;
}

/**
 * 与 deploy/Install.md 中的本地 API 演示学生保持一致。
 * 这些数据只用于本地联调，不可用于生产环境。
 */
export const patientDemoAccounts: PatientDemoAccount[] = [
  { name: '陈小雨', idCardNo: '110101194803120010', phone: '13800000001' },
  { name: '周子墨', idCardNo: '110101195507250026', phone: '13800000002' },
  { name: '林可儿', idCardNo: '110101194011020038', phone: '13800000003' },
  { name: '赵一鸣', idCardNo: '110101196801180043', phone: '13800000004' },
  { name: '吴思远', idCardNo: '110101198509300051', phone: '13800000005' },
  { name: '郑小满', idCardNo: '110101197206150028', phone: '13800000006' },
  { name: '钱嘉树', idCardNo: '110101196212080035', phone: '13800000007' },
  { name: '冯乐怡', idCardNo: '110101197904220026', phone: '13800000008' },
  { name: '韩宇轩', idCardNo: '110101195010090019', phone: '13800000009' },
  { name: '苏晚晴', idCardNo: '11010119920214002X', phone: '13800000010' },
];
