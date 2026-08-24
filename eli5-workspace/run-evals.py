#!/usr/bin/env python3
from __future__ import annotations

"""ELI5-CN Skill 评测脚本

对每个测试用例分别用「装了 skill」和「裸模型（baseline）」运行，再用 Claude 自动逐条评分。

前置条件：
  - 已安装 claude CLI（npm install -g @anthropic-ai/claude-code）
  - skill 文件已就位（默认读取 ~/.claude/skills/eli5-cn/SKILL.md）

用法：
  # 默认：skill vs baseline 对比
  python run-evals.py

  # A/B 对比两个版本的 skill
  python run-evals.py --a skills/eli5-cn/SKILL.md --b ~/experiments/SKILL-v2.md

  # 自定义 A/B 标签
  python run-evals.py --a skills/eli5-cn/SKILL.md --a-label current --b ~/new/SKILL.md --b-label rewrite

  # 只测 skill，不做对比
  python run-evals.py --a skills/eli5-cn/SKILL.md

  # 其他选项
  python run-evals.py --test=1           # 只跑第 1 个用例
  python run-evals.py --grade-only       # 只评分，不重新运行

改编自 https://github.com/dreambigou/eli5 的同名脚本（MIT License）。
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EVALS_JSON = SCRIPT_DIR / "evals.json"
DEFAULT_SKILL = Path.home() / ".claude" / "skills" / "eli5-cn" / "SKILL.md"


def load_evals():
    with open(EVALS_JSON, encoding="utf-8") as f:
        return json.load(f)["evals"]


def find_iteration(grade_only: bool) -> int:
    iteration = 1
    if grade_only:
        while (SCRIPT_DIR / f"iteration-{iteration + 1}").is_dir():
            iteration += 1
    else:
        while (SCRIPT_DIR / f"iteration-{iteration}").is_dir():
            iteration += 1
    return iteration


def run_claude(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  claude CLI 错误: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout.strip()


def run_test(eval_case: dict, outdir: Path, configs: list[dict]):
    name = eval_case["name"]
    prompt = eval_case["prompt"]
    print(f"--- Test {eval_case['id'] + 1}: {name} ---")

    for config in configs:
        config_dir = outdir / name / config["dir_name"] / "outputs"
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"  [{config['label']}] Running...")
        start = time.time()
        if config["skill_path"]:
            response = run_claude(
                f"Read the skill at {config['skill_path']} first, then follow its instructions. Task: {prompt}"
            )
        else:
            response = run_claude(prompt)
        elapsed = time.time() - start
        (config_dir / "response.md").write_text(response, encoding="utf-8")
        (config_dir.parent / "timing.json").write_text(
            json.dumps({"seconds": round(elapsed, 2)}), encoding="utf-8"
        )
        print(f"  [{config['label']}] Done ({elapsed:.1f}s)")

    print()


def grade_response(response_file: Path, assertions: list[str]) -> str:
    response_content = response_file.read_text(encoding="utf-8")
    assertions_text = "\n".join(
        f"{i + 1}. {a}" for i, a in enumerate(assertions)
    )
    return run_claude(
        f"""你是一位严格到近乎苛刻的评分员。请根据每条断言对下面的回答逐条评分。

评分规则：
- 只有回答中「明确、直接」体现了断言要求，才给 PASS。仅仅是「隐含」「接近」「大意如此」「算做到了」一律给 FAIL。
- 每条断言里的每个要素都必须满足；有多个要素（①②③④ 或「A/B/C」）时，缺任何一个都判 FAIL。
- 证据必须引用回答中的具体原文片段；引不出原文就判 FAIL。
- 不要因为回答整体写得不错就放宽标准，只对照断言的硬性要求。

回答内容：
{response_content}

断言列表：
{assertions_text}

对每条断言，输出恰好一行：
PASS|<序号>|<引用原文的简要证据>
或
FAIL|<序号>|<缺失的具体要素>

只输出这些行，不要输出任何其他内容。"""
    )


def parse_grades(grade_output: str, expected_count: int) -> list[tuple[str, str, str]]:
    results = []
    for line in grade_output.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            verdict = parts[0].strip()
            if verdict in ("PASS", "FAIL"):
                raw_num = parts[1].strip().strip("<>#")
                results.append((verdict, raw_num, parts[2].strip()))
                if len(results) == expected_count:
                    break
    return results


def grade_all(evals: list[dict], outdir: Path, configs: list[dict], test_filter: int | None):
    print("=== 开始评分 ===\n")

    # 每个 config 的通过数统计
    totals = {c["dir_name"]: {"pass": 0, "total": 0} for c in configs}

    for eval_case in evals:
        if test_filter is not None and eval_case["id"] != test_filter:
            continue

        name = eval_case["name"]
        assertions = eval_case["assertions"]
        print(f"--- Test {eval_case['id'] + 1}: {name} ---")

        for config in configs:
            response_file = outdir / name / config["dir_name"] / "outputs" / "response.md"
            if not response_file.exists():
                continue

            print(f"  [{config['label']}]")
            grade_output = grade_response(response_file, assertions)
            grading_dir = outdir / name / config["dir_name"]
            (grading_dir / "grading.txt").write_text(grade_output, encoding="utf-8")

            grades = parse_grades(grade_output, len(assertions))
            grade_data = []
            for verdict, num, evidence in grades:
                print(f"    {verdict}  #{num} — {evidence}")
                grade_data.append({"assertion": int(num), "verdict": verdict, "evidence": evidence})
                totals[config["dir_name"]]["total"] += 1
                if verdict == "PASS":
                    totals[config["dir_name"]]["pass"] += 1

            (grading_dir / "grading.json").write_text(
                json.dumps(grade_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        print()

    # 汇总
    iteration_num = outdir.name.split("-")[-1]
    print("=========================================")
    print(f"  通过率汇总 — Iteration {iteration_num}")
    print("=========================================")

    rates = {}
    for config in configs:
        t = totals[config["dir_name"]]
        if t["total"] > 0:
            rate = t["pass"] * 100 / t["total"]
            rates[config["dir_name"]] = rate
            print(f"  {config['label']:15s} {t['pass']}/{t['total']} passed ({rate:.1f}%)")

    if len(rates) == 2:
        keys = list(rates)
        delta = rates[keys[0]] - rates[keys[1]]
        print(f"  {'Delta':15s} {delta:+.1f}%")

    print("=========================================")

    # 保存汇总
    summary_lines = [
        f"ELI5-CN Eval Summary — Iteration {iteration_num}",
        f"Date: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for config in configs:
        t = totals[config["dir_name"]]
        if t["total"] > 0:
            summary_lines.append(f"{config['label']}: {t['pass']}/{t['total']} passed")
    (outdir / "summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    # 保存配置元数据
    config_meta = {
        "configs": [
            {"label": c["label"], "dir_name": c["dir_name"],
             "skill_path": str(c["skill_path"]) if c["skill_path"] else None}
            for c in configs
        ]
    }
    (outdir / "config.json").write_text(
        json.dumps(config_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"\n评分详情: {outdir}/*/<config>/grading.txt")


def build_configs(args) -> list[dict]:
    """根据命令行参数构建要运行的配置列表。"""
    configs = []

    if args.a and args.b:
        # A/B 对比：两个 skill 版本
        configs.append({
            "label": args.a_label or "A",
            "dir_name": args.a_label or "a",
            "skill_path": Path(args.a).resolve(),
        })
        configs.append({
            "label": args.b_label or "B",
            "dir_name": args.b_label or "b",
            "skill_path": Path(args.b).resolve(),
        })
    elif args.a:
        # 单个 skill，不做对比
        configs.append({
            "label": args.a_label or "skill",
            "dir_name": "with_skill",
            "skill_path": Path(args.a).resolve(),
        })
    else:
        # 默认：已安装的 skill vs baseline
        configs.append({
            "label": "with skill",
            "dir_name": "with_skill",
            "skill_path": DEFAULT_SKILL,
        })
        configs.append({
            "label": "baseline",
            "dir_name": "without_skill",
            "skill_path": None,
        })

    return configs


def main():
    parser = argparse.ArgumentParser(description="ELI5-CN Skill 评测脚本")
    parser.add_argument("--test", type=int, help="只跑第 N 个用例（从 1 开始）")
    parser.add_argument("--grade-only", action="store_true", help="只评分，不重新运行")
    parser.add_argument("--a", metavar="PATH", help="skill 版本 A 的路径")
    parser.add_argument("--a-label", metavar="LABEL", help="版本 A 的标签（默认 'A'）")
    parser.add_argument("--b", metavar="PATH", help="skill 版本 B 的路径")
    parser.add_argument("--b-label", metavar="LABEL", help="版本 B 的标签（默认 'B'）")
    args = parser.parse_args()

    if args.b and not args.a:
        parser.error("--b 需要与 --a 一起使用")

    configs = build_configs(args)
    evals = load_evals()
    iteration = find_iteration(args.grade_only)
    outdir = SCRIPT_DIR / f"iteration-{iteration}"

    test_filter = (args.test - 1) if args.test else None

    print("=== ELI5-CN Eval Runner ===")
    print(f"输出目录: {outdir}")
    for c in configs:
        src = c["skill_path"] or "(无 skill)"
        print(f"  {c['label']}: {src}")
    print()

    # 检查前置条件
    if not args.grade_only:
        if subprocess.run(["which", "claude"], capture_output=True).returncode != 0:
            print("错误：未找到 'claude' CLI。安装方式：npm install -g @anthropic-ai/claude-code")
            sys.exit(1)
        for c in configs:
            if c["skill_path"] and not c["skill_path"].exists():
                print(f"错误：skill 文件不存在于 {c['skill_path']}")
                sys.exit(1)

        for eval_case in evals:
            if test_filter is not None and eval_case["id"] != test_filter:
                continue
            run_test(eval_case, outdir, configs)

        print("=== 运行完毕 ===\n")

    grade_all(evals, outdir, configs, test_filter)
    print("\n=== 全部完成！===")


if __name__ == "__main__":
    main()
