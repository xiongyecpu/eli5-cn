# ELI5-CN

> 两个配套的中文本土化 Agent Skill，把任何复杂话题讲清楚：一个**画**给人看，一个**讲**给人听。

| Skill | 定位 | 触发方式 |
|-------|------|---------|
| **`eli5-cn`** | 图解版——HTML 大图、少字 | 「画个图」「图解一下」「一张图解释」 |
| **`eli5-talk`** | 文字版——受众适配地讲 | 「给我妈讲讲」「说人话」「怎么跟领导解释」 |

两个 skill 分开安装、分开触发，各管各的：**要图解用 eli5-cn，要讲解用 eli5-talk**。

---

## 📊 eli5-cn —— 图解版（画给人看）

把任何概念、代码、流程或系统，画成一张 **HTML 大图**：大图、少字，讲给一个对此完全不懂的人。

核心指令源自 [Thariq Shihipar 的 `/eli5`](https://wangruofeng007.com/blog/2026-08/eli5-skill-deconstruct/)（Anthropic 内部疯传的做图 skill，MIT）：

> Explain like I'm someone who knows nothing about this topic, using a HTML artifact with big pictures and few words.

规则：自包含 HTML（内联 CSS + 大号 emoji/SVG，无外部图片）· 每张卡片一个大图 + 一句话 · 3-7 张卡片 · 收尾一句总结比喻 · 能画就不写。

```
画个图，解释一下手机支付的钱是怎么到商家账上的
图解一下 DNS 是怎么工作的
把太阳系画成一张图给孩子看
```

---

## 💬 eli5-talk —— 文字版（讲给人听）

用对方熟悉的世界把话说清楚。根据受众（孩子、爸妈、爷爷奶奶、领导、同事、客户……）自动调整语气、词汇、类比和深度。

灵感来自 [dreambigou/eli5](https://github.com/dreambigou/eli5)，重做成中文语境，并加了三个特化机制：

- **爸爸视角·十万个为什么**：处理 5 岁好奇宝宝的连环追问，目标排序是 **保护好奇心 > 一起探索 > 知识准确**。六条原则里最关键的是「答案只给一层」和「允许说不知道」——严禁敷衍（"本来就是这样"）和甩开（"长大你就懂了"）。
- **防诈骗预判**：给长辈解释涉及钱、手机、账号、AI 的新事物时，主动接住"这是不是骗人的"——先肯定警惕心、再区分概念与骗局、给一条可执行的自保建议，绝不说"很安全您别担心"的空话。
- **一句话汇报版**：给领导的解释结尾附赠一句可直接转发的版本。

```
我女儿5岁，问为什么月亮一直跟着我们走，怎么回答
我儿子问飞机为什么能飞，我自己也说不清，怎么办
给我妈讲讲什么是AI大模型
我爷爷问手机支付安不安全，怎么跟他说
怎么跟领导解释为什么要花两周重构代码
```

### 支持的受众

| 类别 | 例子 |
|------|------|
| **家庭关系** | 孩子、爸妈、爷爷奶奶/外公外婆、配偶、饭桌上的亲戚 |
| **职场角色** | 领导/老板、体制内领导、HR/财务等非技术同事、甲方/客户、技术同事 |
| **年龄** | 5-10 岁、11-17 岁、18-30 岁、30-50 岁、50+ |
| **教育背景** | 小学生、中学生、大学生、研究生/专业人士 |

### 其他设计

- **中文类比素材库**：厨房、菜市场、存折、盖章审批、装修、挂号、家族群……不用 crayons 和 playground。
- **禁用清单**：不居高临下、不堆互联网黑话（抓手闭环赋能）、不硬凹过时热梗、不用失真的类比。

---

## 安装

```bash
git clone https://github.com/xiongyecpu/eli5-cn.git
cp -r eli5-cn/skills/eli5-cn ~/.claude/skills/eli5-cn      # 图解版
cp -r eli5-cn/skills/eli5-talk ~/.claude/skills/eli5-talk  # 文字版
```

然后在 Claude Code 里直接说「画个图解释……」「我女儿问为什么……」「给我妈讲讲……」即可触发对应 skill。

## 评测

**前置条件**：已安装 [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)。

两个 skill 各有一份测试用例：文字版 `evals.json`（9 用例），图解版 `evals-pic.json`（1 用例）。

```bash
# 文字版 eli5-talk：skill vs baseline 对比
python eli5-workspace/run-evals.py

# 图解版 eli5-cn：单 skill 评测
python eli5-workspace/run-evals.py --evals eli5-workspace/evals-pic.json \
    --a ~/.claude/skills/eli5-cn/SKILL.md

# 其他选项
python eli5-workspace/run-evals.py --test=1          # 只跑第 1 个用例
python eli5-workspace/run-evals.py --grade-only      # 只评分不重跑
python eli5-workspace/run-evals.py --a A.md --b B.md # A/B 对比
```

脚本做三件事：① 每个 prompt 跑两遍（带 skill / 裸模型 baseline）② 用 Claude 按断言逐条严格评分 ③ 输出通过率对比。结果保存在 `eli5-workspace/iteration-N/`。

### 文字版 eli5-talk 当前结果（iteration-5，2026-08-24）

9 个用例 × 4 条断言 = 36 项检查点：

| 配置 | 通过 | 通过率 |
|------|------|--------|
| 带 skill | 34/36 | 94.4% |
| 裸模型（baseline） | 27/36 | 75.0% |
| **增益** | | **+19.4%** |

| 用例 | 场景 | 带 skill | 裸模型 |
|------|------|:---:|:---:|
| 月亮为什么跟着走 | 十万个为什么 | 4/4 | 4/4 |
| **爸爸也不会（飞机为什么能飞）** | 十万个为什么 | **4/4** | **2/4** |
| AI 大模型 → 妈妈 | 防诈骗预判 | 3/4 | 2/4 |
| 手机支付 → 爷爷 | 防诈骗预判 | 4/4 | 3/4 |
| 重构 → 领导 | 一句话汇报版 | 4/4 | 3/4 |
| 推荐算法 → 15 岁 | 青少年 | 4/4 | 3/4 |
| 数据库 → HR | 职场 | 3/4 | 3/4 |
| 数据上云 → 体制内 | 职场 | 4/4 | 4/4 |
| 通货膨胀（默认受众） | 默认父母辈 | 4/4 | 3/4 |

**增益最大的是「爸爸也不会」**：裸模型硬答了牛顿第三定律，带 skill 后才做到「承认不知道 + 一起找答案」，4/4 vs 2/4。

> 注：带 skill 的 2 个 FAIL 源于断言过度要求——「解释大模型/数据库时主题词本身零出现」，属断言设计问题，后续改为「除主题词外零额外术语」。

### 新增测试用例

在 `eli5-workspace/evals.json`（文字版）或 `evals-pic.json`（图解版）的 `evals` 数组中加一条（`id` 从 0 递增），每条含 `prompt`、`name`、`audience` 和 4 条 `assertions`。

## 致谢

- 图解版灵感：[Thariq Shihipar 的 `/eli5`](https://wangruofeng007.com/blog/2026-08/eli5-skill-deconstruct/)（MIT）
- 文字版灵感与评测框架：[dreambigou/eli5](https://github.com/dreambigou/eli5)（MIT）

## License

MIT
