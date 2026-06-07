# Tutor From Zero

一个面向大学课程复习的跨智能体 Agent Skill。

它不是简单压缩课件的「总结器」，而是一位从零基础开始、会诊断学情、拆解概念、带着做题、记录错题并持续跟进的交互式家教。同时，它也能从 PPTX、DOCX、PDF 和扫描资料中提取内容，生成复习讲义、练习题、模拟卷、考前速记卡和离线 HTML 复习站点。

本 Skill 遵循 [Agent Skills 开放规范](https://agentskills.io/)，可用于支持该规范的智能体，例如 Claude Code、Cursor、TRAE、Codex 等。

## 核心能力

- **零基础交互教学**：先讲直觉，再讲定义、逻辑、推导、例题和常见误区。
- **课程资料提取**：支持 PPTX、DOCX、文本型 PDF、扫描型 PDF 和常见图片。
- **中英文 OCR**：通过 Tesseract 识别扫描课件、截图和图片型 PDF。
- **材料可信度分析**：区分真题、作业、课堂记录、课件和非正式信息的证据强度。
- **分级练习**：提供 L1 概念验证、L2 综合应用和 L3 模拟考试。
- **错题与进度管理**：保存章节掌握度、薄弱知识点、错误原因和下一步任务。
- **自适应复习模式**：根据考试日期自动选择完整、压缩或三天内紧急模式。
- **复习资料生成**：输出 Markdown 讲义、题库、模拟卷、速记卡和离线 HTML。
- **隐私优先**：课程原始材料在本地处理，不应上传到第三方搜索或在线服务。

## 教学理念

Tutor From Zero 遵循四个原则：

1. **不是看过，而是能讲出来。**
2. **不是给答案，而是教会怎么想到答案。**
3. **不是平均用力，而是优先处理高信号、高分值内容。**
4. **不知道就明确说不知道，不把推测包装成老师的真实出题偏好。**

每个重要知识点通常使用以下教学结构：

```text
直觉理解
  -> 精确定义
  -> 逻辑拆解
  -> 推导或论据
  -> 例题演示
  -> 常见误区与考试陷阱
```

## 目录结构

```text
tutor-from-zero/
├── SKILL.md                    # Agent Skill 主入口
├── README.md                   # GitHub 项目说明
├── LICENSE                     # CC BY-NC 4.0
├── THIRD_PARTY_NOTICES.md      # 第三方来源与许可证说明
├── requirements.txt
├── scripts/
│   ├── tutor.py                # 统一命令行入口
│   ├── doctor.py               # 环境与 OCR 诊断
│   ├── extract_materials.py    # 课程材料扫描和提取
│   ├── extract_pdf.py
│   ├── extract_docx.py
│   ├── extract_pptx.py
│   ├── image_extractor.py
│   ├── ocr.py
│   ├── progress.py             # 学习进度的原子化存储
│   └── render_outputs.py       # 离线 HTML 渲染
├── references/                 # 按需加载的教学协议
├── assets/templates/           # HTML 样式和模板
└── tests/
```

## 环境要求

- Python 3.10 或更高版本
- 课程目录的读写权限
- 使用 OCR 时需要：
  - Tesseract OCR
  - `chi_sim` 简体中文语言包
  - `eng` 英文语言包

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

检查当前环境：

```bash
python scripts/tutor.py doctor
```

如果不处理扫描件，PPTX、DOCX 和带文本层的 PDF 仍可正常提取。`doctor` 会明确报告缺少的 Tesseract 程序或语言包。

## 配置为 Agent Skill

将整个 `tutor-from-zero` 文件夹复制到智能体支持的 Skill 目录。不同平台的常见项目级路径如下：

| 平台 | 常见路径 |
|---|---|
| Claude Code | `.claude/skills/tutor-from-zero/` |
| Cursor | `.cursor/skills/tutor-from-zero/` |
| TRAE | `.agents/skills/tutor-from-zero/` |
| Codex | `.agents/skills/tutor-from-zero/` 或用户 Skill 目录 |

各平台的目录约定可能随版本变化，请以对应平台的最新文档为准。Skill 的核心入口始终是：

```text
tutor-from-zero/SKILL.md
```

也可以在支持显式 Skill 调用的平台中直接使用：

```text
使用 $tutor-from-zero 带我从零复习数据结构。
```

## 快速开始

假设课程资料位于：

```text
D:\Courses\DataStructures
```

### 1. 检查环境

```bash
python scripts/tutor.py doctor
```

### 2. 提取课程材料

```bash
python scripts/tutor.py extract "D:\Courses\DataStructures" --exam-date 2026-06-20
```

提取后会在课程目录生成：

```text
DataStructures/
└── .tutor/
    ├── manifest.json
    ├── extraction_bundle.json
    ├── progress.json
    └── cache/
```

### 3. 查看学习状态

```bash
python scripts/tutor.py status "D:\Courses\DataStructures"
```

### 4. 渲染复习站点

当智能体在 `outputs/` 中生成复习 Markdown 后，运行：

```bash
python scripts/tutor.py render "D:\Courses\DataStructures"
```

输出文件：

```text
DataStructures/outputs/review-site.html
```

### 5. 验证课程工作区

```bash
python scripts/tutor.py validate "D:\Courses\DataStructures"
```

## 课程目录中的持久化文件

`.tutor/progress.json` 是唯一权威的学习状态文件，主要记录：

- 考试日期和当前复习模式；
- 各章节的学习状态；
- 已掌握和薄弱的概念；
- 当前练习等级与正确率；
- 错题、错误原因和复习状态；
- 学习偏好、最近会话摘要和下一步任务。

写入进度时会采用临时文件替换并保留备份，降低中断或文件损坏导致状态丢失的风险。

## 三种复习模式

| 模式 | 触发条件 | 策略 |
|---|---|---|
| `full` | 距考试至少 8 天或未提供日期 | 完整教学、分级练习、综合复习和模拟考试 |
| `compressed` | 距考试 4 至 7 天 | 核心章节完整讲解，次要内容压缩覆盖 |
| `emergency` | 距考试不超过 3 天 | 必考概念链、真题优先、精简模拟和最后速记 |

紧急模式代表优先级压缩，不代表省略理解和胡乱押题。

## 材料与置信度

默认材料优先级：

```text
历年真题与作业
  > 课堂录音、讲课记录和教师笔记
  > PPT、教学大纲和教材
  > 群聊、截图和非正式回忆
```

生成内容应区分：

- 课程材料直接确认的事实；
- 多份材料共同支持的推断；
- 用于解释概念的公开背景资料；
- 证据不足的猜测。

网络搜索只能补充公开信息，不能把本地材料中的私密内容作为搜索词，也不能把通用网络资料当作本校老师真实出题范围的证明。

## 运行测试

```bash
python -m pytest -q
```

当前测试覆盖：

- PPTX、DOCX 和 PDF 提取；
- 扫描 PDF 的 OCR 回退；
- 损坏文件处理；
- 学习模式日期边界；
- 进度文件创建、备份和恢复；
- 材料清单与信号等级；
- Markdown 到 HTML 渲染；
- Agent Skills 目录和引用完整性。

## 隐私与版权

- 不要将未公开试卷、录音、群聊、个人信息或完整课件上传到第三方服务。
- 使用课程材料前，请确认自己拥有合法的学习、处理和分享权限。
- 生成复习资料时优先概括和解释，避免大段复制教材或受限制内容。
- 本项目不会保证考试通过，也不会把推测伪装为教师的正式说明。

## 许可证

本项目包含基于 ExamPass Assistant 改编的内容，因此整体按
[Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)
进行非商业分发。

你可以在满足署名和非商业条件的前提下使用、修改和分享本项目。商业使用前需要另行处理相关授权。

其他参考项目和许可证信息见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 致谢

本项目综合并重新组织了以下本地项目中的方法与实现：

- ExamPass Assistant
- final-exam-review
- professor-skill
- professor-synapse

其中无明确许可证的来源只用于启发通用设计，没有直接再分发其代码或原文。
