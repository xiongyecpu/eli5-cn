# ELI5-CN —— 说人话

> 一个中文本土化的 Agent Skill：把任何复杂话题，用对方熟悉的世界讲清楚。根据受众（爸妈、爷爷奶奶、孩子、领导、同事、客户……）自动调整语气、词汇、类比和深度。

灵感来自 [dreambigou/eli5](https://github.com/dreambigou/eli5)。不是翻译，是重做——类比换成了中国生活场景，新增了中国特色的「防诈骗预判」和「一句话汇报版」机制。

## 什么时候会用到

```
给我妈讲讲什么是AI大模型
怎么跟领导解释为什么要花两周重构代码
我爷爷问手机支付安不安全，怎么跟他说
给我15岁的侄子解释为什么短视频App知道他想看什么
我女儿5岁，问为什么月亮一直跟着我们走，怎么回答
用大白话解释一下什么是区块链
```

## 支持的受众

| 类别 | 例子 |
|------|------|
| **家庭关系** | 爸妈、爷爷奶奶/外公外婆、孩子、配偶、饭桌上的亲戚 |
| **职场角色** | 领导/老板、体制内领导、HR/财务等非技术同事、甲方/客户、技术同事 |
| **年龄** | 5-10 岁、11-17 岁、18-30 岁、30-50 岁、50+ |
| **教育背景** | 小学生、中学生、大学生、研究生/专业人士 |

## 相比原版的差异化设计

- **爸爸视角·十万个为什么**：专门处理 5 岁好奇宝宝的连环追问——目标排序是「保护好奇心 > 一起探索 > 知识准确」。答案只给一层、用他眼前的东西类比、反问回去、允许说"不知道我们一起查"、能动手做实验就不光讲。明确禁止好奇心的两大杀手：敷衍（"本来就是这样"）和甩开（"长大你就懂了"）。
- **防诈骗预判**：给长辈解释涉及钱、手机、账号、AI 的新事物时，主动接住"这是不是骗人的"的警惕心——先肯定、再区分概念与骗局、最后给一条马上能用的自保建议。绝不说"很安全您别担心"这种空话。
- **一句话汇报版**：职场场景结尾附赠可以直接转发给领导的版本。
- **中文类比素材库**：厨房、菜市场、存折、盖章审批、装修、挂号、家族群……不用 crayons 和 playground。
- **禁用清单**：不居高临下、不堆互联网黑话（抓手闭环赋能）、不硬凹过时热梗、不用失真的类比。

## 安装

```bash
git clone https://github.com/xiongyecpu/eli5-cn.git
cp -r eli5-cn/skills/eli5-cn ~/.claude/skills/eli5-cn
```

然后在 Claude Code 里直接说「给我妈讲讲……」「怎么跟领导解释……」即可触发。

## 评测

测试用例在 `eli5-workspace/evals.json`，覆盖家庭和职场两大场景，每个用例 4 条可验证断言。

**前置条件**：已安装 [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)，且 skill 已安装到 `~/.claude/skills/eli5-cn/`。

```bash
# 跑全部用例 + 自动评分（skill vs baseline 对比）
python eli5-workspace/run-evals.py

# 只跑一个用例
python eli5-workspace/run-evals.py --test=1

# A/B 对比两个版本的 skill
python eli5-workspace/run-evals.py --a skills/eli5-cn/SKILL.md --b ~/experiments/SKILL-v2.md

# 只评分不重跑
python eli5-workspace/run-evals.py --grade-only
```

脚本做三件事：

1. 每个 prompt 跑两遍——一遍带 skill，一遍裸模型（baseline）
2. 用 Claude 按断言逐条自动评分
3. 输出通过率对比汇总

结果保存在 `eli5-workspace/iteration-N/`，每次运行自动递增。

### 新增测试用例

在 `eli5-workspace/evals.json` 的 `evals` 数组中加一条（`id` 从 0 开始递增）：

```json
{
  "id": 6,
  "name": "explain-vpn-to-dad",
  "prompt": "我爸问VPN是什么，怎么用大白话解释",
  "audience": "爸爸",
  "assertions": [
    "断言1……",
    "断言2……",
    "断言3……",
    "断言4……"
  ]
}
```

## 致谢

- 原版 skill 与评测框架：[dreambigou/eli5](https://github.com/dreambigou/eli5)（MIT）
- 原版构建过程博客：[Building an ELI5 Skill for Claude](https://andrewou.pages.dev/posts/building-an-eli5-skill-for-claude/)

## License

MIT
