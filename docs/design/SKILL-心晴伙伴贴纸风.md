---
name: xinqing-sticker-ui
description: 心晴伙伴青少年心理护航系统的前端视觉规范（A 卡通治愈贴纸风）。当需要新建、改写、评审本项目任何界面（学生端/老师端/家长端，React + Tailwind v4），或需要实现"贴纸风/治愈系/面向青少年且去医疗化"的中文界面时使用；也适用于把其它风格改成该风格、或检查页面是否违反去 AI 味规则。
---

# 心晴伙伴 · 贴纸风前端规范（Agent Skill）

## 何时用

- 给本项目加新页面/新组件、改视觉、评审"像不像 AI 生成的"
- 任何需要「给青少年看、温柔、去医疗化」的中文界面
- 把手头页面"翻译"成同一套视觉语言

## 一句话心法

**奶油纸 + 墨色 2.5px 描边 + 0 模糊硬投影 + 薄荷/蜜桃/柠檬三强调色；像贴纸手账，不像医疗系统。**

学生端 430px 手机框、对话优先；老师端克制版（同配色、高密度、去贴纸倾斜）；家长端与老师端同族。

## Token（复制即用）

```css
:root {                    /* 老师端 / 全站 */
  --background:#FFF6EC; --surface:#FFFFFF; --surface-secondary:#FFF9F2;
  --foreground:#2A2320; --foreground-muted:#6B5F53; --border:#EDDFC9;
  --primary:#2E8B6A; --primary-tint:#E2F8EC;
  --accent-mint:#7FDBB6; --accent-peach:#FFB5A7; --accent-lemon:#FFD66B; --accent-sky:#A9C9DE;
  --ink:#2A2320; --danger:#EF6A63;
  --font-sans:'Noto Sans SC','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
}
.patient-app {             /* 学生端覆盖：同一套值 + 波点底 */
  --background:#FFF6EC; --primary:#35A278;
  background:
    radial-gradient(circle at 3px 3px, rgb(213 180 138 / 18%) 1.7px, transparent 1.8px),
    var(--background);
  background-size:28px 28px, auto;
  font-family:var(--font-sans);
}
h1,h2 { font-weight:800; letter-spacing:-0.035em; }   /* 学生端用 900 */
```

## 组件骨架（照抄）

```css
.patient-card         { border:2.5px solid var(--ink); border-radius:22px; background:#fff; box-shadow:6px 6px 0 var(--ink); }
.patient-card-soft    { border:2.5px solid var(--ink); border-radius:22px; background:#fff; box-shadow:7px 7px 0 var(--accent-mint); }
.patient-card-sticker { border:2.5px dashed var(--ink); border-radius:20px; background:#FFFBF4; box-shadow:5px 5px 0 var(--accent-lemon); }
.patient-primary-button {
  display:inline-flex; min-height:50px; align-items:center; justify-content:center; gap:8px;
  border:2.5px solid var(--ink); border-radius:999px; background:var(--accent-mint);
  color:var(--ink); font-weight:900; box-shadow:4px 4px 0 var(--ink);
  transition:transform .16s ease, box-shadow .16s ease;
}
.patient-primary-button:hover  { transform:translate(-1px,-1px); box-shadow:5px 5px 0 var(--ink); }
.patient-primary-button:active { transform:translate(2px,2px); box-shadow:1px 1px 0 var(--ink); }
.patient-field        { min-height:56px; border:2.5px solid var(--ink); border-radius:14px; background:#fff; }
.patient-field:focus-within { border-color:var(--primary); background:var(--surface-secondary); box-shadow:none; }
.patient-sticker-tag  { display:inline-block; border:2.5px solid var(--ink); border-radius:12px; padding:4px 13px;
                        font-size:12px; font-weight:900; background:var(--accent-peach);
                        box-shadow:2.5px 2.5px 0 var(--ink); transform:rotate(-2.5deg); }
.patient-highlight    { background:linear-gradient(transparent 58%, var(--accent-lemon) 58%); font-weight:800; }
.patient-progress-track { height:14px; border:2.5px solid var(--ink); border-radius:999px; background:#fff; overflow:hidden; }
.patient-progress-value { height:100%; background:var(--accent-mint); }
```

Tailwind 里怎么用：颜色走 `var(--accent-*)`（如 `bg-[var(--accent-mint)]`），描边用 `border-[2.5px] border-[var(--ink)]`，硬投影用 `shadow-[6px_6px_0_var(--ink)]`。

## 硬规则（违反即不合格）

1. 禁渐变（唯一例外：荧光笔高亮、语音球内部着色）
2. 禁玻璃拟态 / `backdrop-blur` 悬浮面板
3. 禁 1px 细线（表单/表格等真实控件除外）
4. 禁柔和阴影 / 发光（投影必须 0 模糊、带偏移）
5. 禁居中小字 eyebrow、禁图标卡片阵列、禁等宽字体
6. 禁纯黑 `#000`、禁紫蓝 AI 渐变、禁外链字体
7. 标题 ≤ 两行；每屏信息密度要够（禁止大面积空白装高级）
8. 两个以上强调色同屏时要有语义分工（薄荷=行动、蜜桃=温柔、柠檬=提示、天蓝=中性）

## 文案纪律（同等重要）

- 学生端**不出现**量表名/筛查主题/诊断词（「抑郁筛查量表」「自杀风险」禁止）
- 用「聊天 / 小卡片 / 老师 / 你」替代「评估 / 宣教 / 护士 / 患者」
- 危机场景：先接住情绪 → 说明会通知心理老师 → 给热线 12356 / 12355；不诊断、不贴标签

## 落地检查清单

```bash
grep -rn "gradient" src/                    # 只应命中 highlight 与语音球
grep -rn "backdrop-blur\|box-shadow: 0 " src/   # 应为 0 命中
grep -rn "<量表名>\|护士\|住院\|患者" src/   # 学生端应为 0 命中
pnpm exec tsc --noEmit
```
再逐页确认：卡片都有 2.5px 描边 + 偏移硬投影；375px 宽下标题不超两行；危机入口可见。

## 参考实现

- token 与组件类：`frontend/src/app/globals.css`（`:root` 与 `.patient-app`）
- 页面样机（10 页，含门厅/登录/对话/任务/手账/老师端/家长端）：`design_mockups/a-full/`
- 详细规范：`docs/design/心晴伙伴-前端设计规范.md`

---

# 附：一页版提示词（可直接粘贴给任意 AI）

```
请为「心晴伙伴·青少年心理护航系统」实现 <页面/组件>，严格遵守以下视觉规范：

风格：A 卡通治愈贴纸风。奶油纸底 #FFF6EC，所有卡片/按钮用 2.5px 墨色 #2A2320 描边，
投影一律为 0 模糊的偏移硬投影（如 6px 6px 0 #2A2320），圆角 20-24px，按钮用胶囊。
强调色分工：薄荷 #7FDBB6 = 主行动；蜜桃 #FFB5A7 = 温柔/贴纸标签（可 rotate -2.5deg）；
柠檬 #FFD66B = 提示与荧光笔高亮；天蓝 #A9C9DE = 中性信息；危险 #EF6A63（浅底 #FFEEEE）。
字体只允许本地中文栈 'Noto Sans SC','PingFang SC','Microsoft YaHei'；标题 900 字重、字距 -0.035em。

严禁：任何渐变（含背景/按钮/文字）、玻璃拟态/backdrop-blur、1px 细线、柔和阴影/发光、
居中小字 eyebrow、图标卡片阵列、等宽字体、纯黑 #000、外链字体、标题超两行、大片空白无内容。

面向 10-18 岁学生：语气温柔平等，像朋友聊天；不得出现量表名、筛查主题、诊断词
（如"抑郁筛查量表""自杀风险"禁止），用"聊天/小卡片/老师/你"替代"评估/宣教/护士/患者"。
涉及危机场景时：先接住情绪 → 说明会通知心理老师 → 给出热线 12356 / 12355；不下诊断、不贴标签。

交付要求：给出可直接运行的代码（本项目为 Next.js + Tailwind v4 + 中文界面），
颜色统一走 CSS 变量（--accent-mint 等），并在结束时逐条自查上述"严禁"清单。
```
