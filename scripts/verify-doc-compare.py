#!/usr/bin/env python3
"""
verify-doc-compare.py — 对比分析报告完整性验证（双向关键词核查版）

用法：
  python3 verify-doc-compare.py --report <报告.md> --docs <对比版文件夹>

检查逻辑：
  正向（漏分析）：遍历预设的特殊股东权利/条款关键词，
                  若对比文件中存在该关键词附近的 [INS]/[DEL]，
                  但报告中未提及该关键词 → 标记为疑似遗漏

  反向（超范围）：提取报告中出现的关键词，
                  若对比文件中该关键词附近无任何 [INS]/[DEL] → 标记为疑似无据分析
"""

import argparse
import zipfile
import re
import sys
from pathlib import Path
from lxml import etree

# ── 预设核查权利清单 ──────────────────────────────────────────────────────────
# 每项格式：(显示名称, [搜索关键词列表], 对报告的最低期望提及词)
RIGHTS_CHECKLIST = [
    ("观察员权利",      ['观察员'],                      ['观察员']),
    ("审计权",          ['审计', '聘请外部审计'],         ['审计']),
    ("知情权/查阅权",   ['知情', '查阅', '检查权'],       ['知情', '查阅']),
    ("回购权",          ['回购'],                        ['回购']),
    ("优先清算权",      ['优先清算', '优先分配额'],        ['清算']),
    ("反稀释权",        ['反稀释', '加权平均'],            ['反稀释']),
    ("优先购买权",      ['优先购买', '优先认购'],          ['优先购买']),
    ("共同出售权",      ['共同出售'],                     ['共同出售']),
    ("领售权",          ['领售', '拖售'],                 ['领售']),
    ("优先分红权",      ['优先分红', '优先获得'],          ['分红']),
    ("董事提名权",      ['提名', '董事'],                 ['董事']),
    ("北交所/新三板排除",['北交所', '新三板', '全国中小企业股份转让'],  ['北交所', '新三板']),
    ("日违约金/违约责任",['日违约金', '违约金', '罚息'],   ['违约金', '违约']),
    ("全职服务义务",    ['全职', '兼职'],                 ['全职']),
    ("基金备案条件",    ['基金备案', '备案'],              ['备案']),
    ("合格上市定义",    ['合格上市'],                     ['合格上市']),
    ("交割先决条件",    ['先决条件', '交割条件'],          ['先决条件', '交割']),
    ("费用承担",        ['律师费', '费用承担', '投资人费用'], ['律师费', '费用']),
]


def extract_change_contexts(docx_path):
    """
    提取对比文件中所有 [INS]/[DEL] 段落的上下文文本
    返回：{'ins': [段落文本...], 'del': [段落文本...]}
    """
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    with zipfile.ZipFile(docx_path) as z:
        with z.open('word/document.xml') as f:
            tree = etree.parse(f)

    body = tree.getroot().find('.//w:body', ns)
    paragraphs = body.findall('.//w:p', ns)

    ins_contexts = []
    del_contexts = []

    for para in paragraphs:
        ins_parts, del_parts, plain_parts = [], [], []

        for elem in para.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'ins':
                t = ''.join(x for x in elem.itertext())
                if t.strip():
                    ins_parts.append(t)
            elif tag == 'del':
                t = ''.join(r.text or '' for r in elem.findall('.//w:delText', ns))
                if t.strip():
                    del_parts.append(t)
            elif tag == 't':
                ptags = [p.tag.split('}')[-1] for p in elem.iterancestors()]
                if 'ins' not in ptags and 'del' not in ptags and elem.text:
                    plain_parts.append(elem.text)

        plain = ''.join(plain_parts)
        ins = ''.join(ins_parts)
        delete = ''.join(del_parts)

        # 段落完整文本（含周围上下文）用于关键词匹配
        full = plain + ins + delete

        if ins:
            ins_contexts.append(full)
        if delete:
            del_contexts.append(full)

    return ins_contexts, del_contexts


def keyword_has_change(keywords, ins_contexts, del_contexts):
    """
    判断关键词列表中任一词是否出现在 [INS] 或 [DEL] 的上下文中
    返回：(found_in_ins, found_in_del, 触发关键词)
    """
    for kw in keywords:
        for ctx in ins_contexts:
            if kw in ctx:
                return True, False, kw
        for ctx in del_contexts:
            if kw in ctx:
                return False, True, kw
    return False, False, None


def keyword_in_report(report_text, expect_keywords):
    """判断期望词是否出现在报告中"""
    return any(kw in report_text for kw in expect_keywords)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True, help='报告 .md 文件路径')
    parser.add_argument('--docs',   required=True, help='对比版文件夹路径')
    args = parser.parse_args()

    report_path = Path(args.report)
    docs_path   = Path(args.docs)

    if not report_path.exists():
        print(f"[错误] 报告文件不存在：{report_path}")
        sys.exit(1)

    docx_files = sorted(set(
        list(docs_path.glob('*对比*.docx')) +
        list(docs_path.glob('*-对比.docx'))
    ))
    if not docx_files:
        docx_files = sorted(set(docs_path.glob('*.docx')))
    docx_files = [f for f in docx_files if not f.name.startswith('~')]

    print("=" * 62)
    print("  对比分析报告完整性验证（双向关键词核查）")
    print("=" * 62)
    print(f"报告：{report_path.name}")
    print(f"文件：{len(docx_files)} 份\n")

    # 合并所有对比文件的变更上下文
    all_ins, all_del = [], []
    for docx in docx_files:
        try:
            ins, dels = extract_change_contexts(docx)
            all_ins.extend(ins)
            all_del.extend(dels)
            print(f"  ✓ {docx.name[:55]}")
        except Exception as e:
            print(f"  ✗ {docx.name}：{e}")

    report_text = open(report_path, encoding='utf-8').read()

    # ── 正向核查（漏分析）────────────────────────────────────────────────────
    print("\n" + "─" * 62)
    print("  正向核查：对比文件有修订 → 报告中是否体现")
    print("─" * 62)
    print(f"  {'条款':20s}  {'文件中有修订?':14s}  {'报告已覆盖?':12s}  {'结论'}")
    print(f"  {'─'*20}  {'─'*14}  {'─'*12}  {'─'*10}")

    forward_issues = []
    for name, search_kws, expect_kws in RIGHTS_CHECKLIST:
        in_ins, in_del, trigger = keyword_has_change(search_kws, all_ins, all_del)
        has_change = in_ins or in_del
        in_report  = keyword_in_report(report_text, expect_kws)

        if has_change:
            change_label = f"{'[INS]' if in_ins else '[DEL]'} ✓"
        else:
            change_label = "无修订"

        if has_change and in_report:
            verdict = "✓ 正常"
        elif has_change and not in_report:
            verdict = "⚠ 疑似遗漏"
            forward_issues.append((name, trigger, change_label))
        elif not has_change and in_report:
            verdict = "△ 核实范围"   # 报告提到但对比文件未见修订
        else:
            verdict = "— 无需分析"

        print(f"  {name:20s}  {change_label:14s}  {'是' if in_report else '否':12s}  {verdict}")

    # ── 反向核查（超范围）────────────────────────────────────────────────────
    print("\n" + "─" * 62)
    print("  反向核查：报告中分析的条款 → 对比文件是否有修订支撑")
    print("─" * 62)

    backward_issues = []
    for name, search_kws, expect_kws in RIGHTS_CHECKLIST:
        in_report = keyword_in_report(report_text, expect_kws)
        if not in_report:
            continue
        in_ins, in_del, _ = keyword_has_change(search_kws, all_ins, all_del)
        has_change = in_ins or in_del
        if not has_change:
            backward_issues.append(name)

    if backward_issues:
        print(f"\n  ⚠ 以下条款出现在报告中，但对比文件未见对应修订标记：")
        for item in backward_issues:
            print(f"     - {item}")
    else:
        print("\n  ✓ 报告中分析的条款均有对应修订标记支撑")

    # ── 汇总 ─────────────────────────────────────────────────────────────────
    print("\n" + "─" * 62)
    print("  汇总")
    print("─" * 62)
    if forward_issues:
        print(f"\n  疑似遗漏 {len(forward_issues)} 项：")
        for name, kw, cl in forward_issues:
            print(f"    ⚠ {name}（触发词：{kw}，{cl}）")
    else:
        print("\n  ✓ 无明显遗漏")

    if backward_issues:
        print(f"\n  疑似超范围分析 {len(backward_issues)} 项：")
        for item in backward_issues:
            print(f"    △ {item}")
    else:
        print("  ✓ 无明显超范围分析")

    # ── 登记表引用 ────────────────────────────────────────────────────────────
    rids = re.findall(r'\bR\d{3}\b', report_text)
    print("\n" + "─" * 62)
    if rids:
        print(f"  登记编号：{sorted(set(rids))}")
    else:
        print("  ⚠ 报告中未发现 R001 格式登记编号（第三点五步修订登记）")

    print("\n" + "=" * 62)
    print("  验证完成")
    print("  注：'△ 核实范围'表示报告提及但对比文件无修订，需确认")
    print("      是否为前轮已有内容的描述性说明（而非分析）")
    print("=" * 62)


if __name__ == '__main__':
    main()
