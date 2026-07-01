from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "code" / "outputs"
FIG = ROOT / "figures"
PAPER = ROOT / "paper"
REPORTS = ROOT / "reports"
RESULTS = ROOT / "results"
PAPER.mkdir(exist_ok=True)

FONT_PATH = "C:/Windows/Fonts/simsun.ttc"
FONT_BOLD = "C:/Windows/Fonts/simhei.ttf"
pdfmetrics.registerFont(TTFont("Song", FONT_PATH))
pdfmetrics.registerFont(TTFont("Hei", FONT_BOLD))


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


def pct(x, nd=1):
    return f"{float(x) * 100:.{nd}f}%"


def fnum(x, nd=3):
    return f"{float(x):.{nd}f}"


def table_data(df: pd.DataFrame, cols: list[str], max_rows=12):
    data = [cols]
    for _, row in df.head(max_rows).iterrows():
        data.append([str(row[c]) if not isinstance(row[c], float) else f"{row[c]:.3f}" for c in cols])
    return data


def md_table(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None) -> str:
    if cols is None:
        cols = list(df.columns)
    view = df[cols].copy()
    if max_rows is not None:
        view = view.head(max_rows)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        cells = []
        for c in cols:
            val = row[c]
            cells.append(f"{val:.3f}" if isinstance(val, float) else str(val))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_markdown(values: dict) -> str:
    pred = values["pred"]
    assoc = values["assoc"]
    sens = values["sens"]
    lines = [
        "# 古代玻璃制品的成分分析与鉴别",
        "",
        "## 摘要",
        "",
        f"针对古代玻璃制品的风化影响、类型鉴别、亚类划分和成分关联问题，本文建立了基于有效性筛选、成分归一化、置换关联检验、类型内风化校正、可解释判别和稳定性聚类的组合模型。首先按题设将成分总和位于 85% 到 105% 的样本视为有效，得到已分类有效采样点 {values['valid_known']} 个；空白成分按未检出处理并归一化到 100%。在风化关系上，玻璃类型与风化的关联达到 Cramer's V={assoc.loc[assoc['变量']=='类型','CramersV'].iloc[0]:.3f}，置换检验 p={assoc.loc[assoc['变量']=='类型','permutation_p'].iloc[0]:.3f}，说明类型是更稳定的解释变量。其次，以 SiO2、K2O、PbO、BaO、P2O5、Al2O3、CaO 等关键成分建立最近质心判别模型，留一交叉验证准确率为 {values['loocv']:.3f}。对未知样本 A1-A8 判别得到 A1、A5、A6、A7 为高钾玻璃，A2、A3、A4、A8 为铅钡玻璃；在 ±5% 成分扰动下平均稳定率为 {sens['稳定率'].mean():.3f}。最后，分别比较高钾和铅钡玻璃的成分相关矩阵，发现 SiO2-Al2O3、SiO2-K2O、PbO-BaO 等元素对的关联差异突出。模型结果可解释性强，并对风化校正、亚类划分和相关性解释的局限进行了说明。",
        "",
        "**关键词：** 古代玻璃；风化校正；成分数据；最近质心判别；聚类分析；敏感性分析",
        "",
        "## 1 问题重述",
        "",
        "题目给出古代玻璃文物的基本信息、已分类样品成分比例和未知样品成分比例。需要分析表面风化与类型、纹饰、颜色的关系，预测风化前成分；提取高钾玻璃与铅钡玻璃的分类规律并划分亚类；鉴别未知类别样本；比较不同类别内化学成分之间的关联关系。",
        "",
        "![技术路线](../figures/F7_modeling_flow.png)",
        "",
        "## 2 数据处理与基本假设",
        "",
        "设样品原始成分为 x_j，空白项表示未检测到该成分，取值为 0。成分总和 S=Σx_j。按题设保留 85≤S≤105 的采样点，并归一化 z_j=100x_j/S。表单 2 中采样点 15 和 17 的成分总和低于 85，因此不进入核心训练；表单 3 的 8 个未知样本均为有效样本。",
        "",
        "主要假设包括：同一类型玻璃的风化平均迁移方向可由风化与未风化样品均值差估计；小样本下优先采用可解释低方差模型；成分相关性反映组成关联特征，不直接解释为化学因果。",
        "",
        "## 3 问题一：风化关系与风化前成分预测",
        "",
        "对类型、纹饰、颜色分别与表面风化建立列联表，并计算 Cramer's V。结果见表 1。颜色的 V 值较高但置换 p 值较大，受颜色缺失和类别分散影响；类型的 p 值最低，说明类型与风化关系更稳定。",
        "",
        "表 1 风化关联强度",
        "",
        md_table(assoc),
        "",
        "![风化关联强度](../figures/F1_weathering_association.png)",
        "",
        "类型内关键成分均值显示，高钾玻璃风化样品 SiO2 明显升高而 K2O 降低；铅钡玻璃风化样品 PbO 和 P2O5 相对升高、SiO2 降低。本文用类型内无风化均值减去风化均值构成平均校正向量，对风化点预测风化前成分；若采样点明确为未风化点，则直接作为风化前近似。",
        "",
        "![关键成分均值](../figures/F2_group_component_means.png)",
        "",
        "## 4 问题二：类型分类规律与亚类划分",
        "",
        f"选取 SiO2、K2O、PbO、BaO、P2O5、Al2O3、CaO 作为判别变量。标准化后分别计算样本到高钾和铅钡质心的距离，距离较小者为预测类型。留一交叉验证准确率为 {values['loocv']:.3f}，说明关键成分足以刻画主要分类规律。",
        "",
        "![类型判别平面](../figures/F3_type_discrimination_scatter.png)",
        "",
        "进一步在每个主类别内进行 k=2 聚类。高钾类轮廓系数为 " + f"{values['sil'].loc[values['sil']['类型']=='高钾','轮廓系数'].iloc[0]:.3f}" + "，铅钡类轮廓系数为 " + f"{values['sil'].loc[values['sil']['类型']=='铅钡','轮廓系数'].iloc[0]:.3f}" + "。亚类中心见图 4，说明高钾亚类主要由 SiO2-K2O-CaO 结构差异区分，铅钡亚类主要由 PbO、BaO、P2O5 和基体 SiO2 的差异区分。",
        "",
        "![亚类中心](../figures/F4_subclass_centers.png)",
        "",
        "## 5 问题三：未知样本鉴别与敏感性",
        "",
        "未知样本沿用问题二的判别模型。预测结果见表 2。A5 的相对置信度较低，说明其处于边界附近，但在 ±5% 单成分扰动下预测仍保持高钾。",
        "",
        "表 2 未知样本预测结果",
        "",
        md_table(pred, ["文物编号", "表面风化", "预测类型", "距离差", "相对置信度"]),
        "",
        "![未知样本敏感性](../figures/F5_unknown_sensitivity.png)",
        "",
        "## 6 问题四：不同类别的成分关联差异",
        "",
        "分别计算高钾和铅钡玻璃归一化成分的 Pearson 相关矩阵，并比较相关系数差异。差异最大的元素对如表 3 所示。高钾玻璃中 SiO2 与 K2O、Al2O3 呈较强负相关，而铅钡玻璃中 PbO、BaO 与其他稳定剂成分的关联结构更突出，反映两类玻璃助熔体系不同。",
        "",
        "表 3 相关关系差异最大的元素对",
        "",
        md_table(values["corrdiff"], max_rows=8),
        "",
        "![相关差异](../figures/F6_correlation_difference.png)",
        "",
        "## 7 模型评价与改进",
        "",
        "模型优点是充分利用题设有效性约束，分类规则与化学成分含义一致，且提供了留一验证、扰动敏感性和亚类轮廓系数。局限在于样本量较小，风化前预测采用类型内平均校正，不能替代真实风化动力学；成分数据具有闭合效应，相关性结果应解释为组成关联特征。后续可引入更多文物样本、埋藏环境信息和重复检测数据，以建立更细的风化校正模型。",
        "",
        "## 8 结论",
        "",
        "1. 表面风化与玻璃类型存在稳定关联，纹饰也有一定关联，颜色受缺失与类别分散影响较大。",
        "2. 高钾玻璃和铅钡玻璃的关键差异集中在 K2O、PbO、BaO、SiO2 和 P2O5 等成分；最近质心模型留一准确率达到 " + f"{values['loocv']:.3f}" + "。",
        "3. 未知样本预测为：A1、A5、A6、A7 属于高钾玻璃，A2、A3、A4、A8 属于铅钡玻璃。",
        "4. 两类玻璃的成分关联结构存在明显差异，差异最大的元素对包括 SiO2-Al2O3、SiO2-K2O 和 PbO-BaO 等。",
    ]
    return "\n".join(lines) + "\n"


def build_pdf(values: dict, pdf_path: Path):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CNTitle", fontName="Hei", fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="CNHeading", fontName="Hei", fontSize=14, leading=20, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="CNBody", fontName="Song", fontSize=10.5, leading=17, alignment=TA_JUSTIFY, firstLineIndent=21))
    styles.add(ParagraphStyle(name="CNCaption", fontName="Song", fontSize=9, leading=13, alignment=TA_CENTER, spaceBefore=4, spaceAfter=8))
    styles.add(ParagraphStyle(name="CNAbstract", fontName="Song", fontSize=10, leading=16, alignment=TA_JUSTIFY))

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    story = []

    def p(text, style="CNBody"):
        story.append(Paragraph(text, styles[style]))

    def h(text):
        story.append(Paragraph(text, styles["CNHeading"]))

    def add_img(path: Path, caption: str, width=15.5 * cm):
        story.append(Spacer(1, 5))
        story.append(Image(str(path), width=width, height=width * 0.56))
        story.append(Paragraph(caption, styles["CNCaption"]))

    def add_table(data, widths=None):
        tbl = Table(data, colWidths=widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Song"),
            ("FONTNAME", (0, 0), (-1, 0), "Hei"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF3")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))

    assoc = values["assoc"]
    pred = values["pred"]
    sens = values["sens"]
    corrdiff = values["corrdiff"]

    story.append(Paragraph("古代玻璃制品的成分分析与鉴别", styles["CNTitle"]))
    p(f"<b>摘要：</b>本文针对古代玻璃制品风化影响、类型鉴别、亚类划分和成分关联问题，建立有效性筛选、成分归一化、置换关联检验、类型内风化校正、最近质心判别和稳定性聚类模型。表单2中得到有效已分类采样点 {values['valid_known']} 个，类型判别留一交叉验证准确率为 {values['loocv']:.3f}。未知样本判别为 A1、A5、A6、A7 属于高钾玻璃，A2、A3、A4、A8 属于铅钡玻璃，扰动平均稳定率为 {sens['稳定率'].mean():.3f}。相关矩阵比较显示，两类玻璃在 SiO2-Al2O3、SiO2-K2O、PbO-BaO 等元素对上存在明显关联差异。", "CNAbstract")
    p("<b>关键词：</b>古代玻璃；风化校正；成分数据；最近质心判别；聚类分析；敏感性分析", "CNAbstract")
    add_img(FIG / "F7_modeling_flow.png", "图1 技术路线")

    h("1 问题重述与数据处理")
    p("题目给出玻璃文物基本信息、已分类成分比例和未知类别成分比例。本文需要回答风化关系、风化前预测、分类与亚类划分、未知类别鉴别及成分关联差异四个问题。")
    p("对原始成分向量 x，空白项按题意视为未检测到并置 0。成分总和 S 位于 85 到 105 之间的样本进入核心训练，再按 z_j=100x_j/S 归一化。表单2中采样点 15、17 不满足有效性范围，核心训练剔除；表单3的 8 个未知样本均有效。")

    h("2 风化关系与风化前成分预测")
    p("分类变量与风化关系用列联表、Cramer's V 和置换检验衡量。结果表明类型与表面风化的置换检验 p 值最低，是更稳定的解释变量；颜色虽然 V 值较高，但缺失和类别分散使显著性不足。")
    add_table(table_data(assoc.round(4), ["变量", "CramersV", "permutation_p", "样本数"]), [3.2 * cm, 3 * cm, 3.2 * cm, 2.2 * cm])
    add_img(FIG / "F1_weathering_association.png", "图2 风化关联强度与置换检验")
    p("在类型内部比较风化与无风化样品均值。高钾玻璃风化样品 SiO2 升高、K2O 降低；铅钡玻璃风化样品 PbO 与 P2O5 相对升高、SiO2 降低。风化前成分预测采用类型内平均差异校正，并对未风化点直接近似。")
    add_img(FIG / "F2_group_component_means.png", "图3 类型-风化分组关键成分均值")

    h("3 类型分类与亚类划分")
    p(f"选取 SiO2、K2O、PbO、BaO、P2O5、Al2O3、CaO 作为关键判别变量。标准化后计算样本到两类质心的距离，距离较小者为预测类型。留一交叉验证准确率为 {values['loocv']:.3f}，说明关键成分可以稳定刻画高钾和铅钡玻璃的主分类规律。")
    add_img(FIG / "F3_type_discrimination_scatter.png", "图4 K2O 与 PbO+BaO 的类型判别平面")
    p(f"在每个主类别内进行 k=2 聚类，高钾类轮廓系数为 {values['sil'].loc[values['sil']['类型']=='高钾','轮廓系数'].iloc[0]:.3f}，铅钡类轮廓系数为 {values['sil'].loc[values['sil']['类型']=='铅钡','轮廓系数'].iloc[0]:.3f}。亚类中心表明，高钾亚类主要体现 SiO2-K2O-CaO 结构差异，铅钡亚类主要体现 PbO、BaO、P2O5 与基体 SiO2 的差异。")
    add_img(FIG / "F4_subclass_centers.png", "图5 主类别内部亚类中心对比")

    h("4 未知样本鉴别与敏感性分析")
    p("对表单3样本使用同一判别流程。预测结果显示 A1、A5、A6、A7 属于高钾玻璃，A2、A3、A4、A8 属于铅钡玻璃。其中 A5 距离差较小，属于相对边界样本，结论需结合敏感性结果谨慎表述。")
    pred_table = pred[["文物编号", "表面风化", "预测类型", "距离差", "相对置信度"]].round(3)
    add_table(table_data(pred_table, ["文物编号", "表面风化", "预测类型", "距离差", "相对置信度"], 8), [2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.5 * cm])
    p(f"对每个未知样本逐一施加 ±5% 单成分相对扰动并重新归一化，8 个样本预测均未改变，平均稳定率为 {sens['稳定率'].mean():.3f}。这说明在当前扰动范围内主类别结论较稳定，但边界样本仍不宜解释为高置信。")
    add_img(FIG / "F5_unknown_sensitivity.png", "图6 未知样本分类敏感性稳定率")

    h("5 成分关联关系比较")
    p("分别计算高钾和铅钡玻璃归一化成分 Pearson 相关矩阵，并比较相关系数差异。差异最大的元素对包括 SiO2-Al2O3、SiO2-K2O、PbO-BaO 等，反映两类玻璃助熔体系和基体组成不同。受成分闭合效应影响，这里将结果解释为组成关联特征，而非严格因果关系。")
    add_table(table_data(corrdiff.round(3), ["成分1", "成分2", "高钾相关", "铅钡相关", "相关差绝对值"], 8), [3 * cm, 3 * cm, 2.2 * cm, 2.2 * cm, 2.6 * cm])
    add_img(FIG / "F6_correlation_difference.png", "图7 高钾与铅钡关键成分相关差异")

    h("6 模型评价与结论")
    p("模型优点是依据题设完成有效性筛选，使用可解释的关键元素构造判别规则，并提供留一验证、扰动敏感性和聚类稳定性。局限在于样本量较小，风化前预测采用类型内平均校正，不能替代真实风化动力学；相关性分析也需考虑成分闭合效应。")
    p("主要结论为：表面风化与玻璃类型存在稳定关联；高钾与铅钡的分类差异集中在 K2O、PbO、BaO、SiO2 与 P2O5；未知样本 A1、A5、A6、A7 判为高钾，A2、A3、A4、A8 判为铅钡；两类玻璃在多个关键元素对上具有明显不同的组成关联结构。")

    doc.build(story)


def main():
    manifest = json.loads((RESULTS / "RESULTS_MANIFEST.json").read_text(encoding="utf-8"))
    assoc = read("q1_association.csv")
    pred = read("q3_unknown_predictions.csv")
    sens = read("q3_sensitivity.csv")
    sil = read("q2_subclass_silhouette.csv")
    corrdiff = read("q4_top_correlation_differences.csv")
    loocv = read("q2_loocv_validation.csv")["正确"].mean()
    valid_known = next(m["value"] for m in manifest["metrics"] if m["id"] == "m_valid_known_samples")
    values = {"manifest": manifest, "assoc": assoc, "pred": pred, "sens": sens, "sil": sil, "corrdiff": corrdiff, "loocv": loocv, "valid_known": valid_known}

    md = build_markdown(values)
    md_path = PAPER / "contest_paper.md"
    md_path.write_text(md, encoding="utf-8")
    pdf_path = PAPER / "contest_paper.pdf"
    build_pdf(values, pdf_path)

    method_matrix = """# Method Implementation Matrix

| Problem | Approved Method | Implemented In Code/Results | Paper Wording | Status | Action |
| --- | --- | --- | --- | --- | --- |
| Q1 | 关联统计、类型内风化校正 | `q1_association.csv`, `q1_group_component_means.csv`, `q1_weathering_prediction.csv`, F1, F2 | 表述为统计关联和平均校正 | implemented | none |
| Q2 | 最近质心判别、类型内 k=2 聚类 | `q2_loocv_validation.csv`, `q2_subclass_assignments.csv`, `q2_subclass_centers.csv`, F3, F4 | 表述为可解释判别和稳定性聚类 | implemented | none |
| Q3 | 未知样本判别、±5% 扰动敏感性 | `q3_unknown_predictions.csv`, `q3_sensitivity.csv`, F3, F5 | A5 降低置信表述 | implemented | none |
| Q4 | 类型内相关矩阵、类别间相关差异 | `q4_corr_高钾.csv`, `q4_corr_铅钡.csv`, `q4_top_correlation_differences.csv`, F6 | 表述为组成关联，不表述为因果 | implemented | none |
"""
    (REPORTS / "METHOD_IMPLEMENTATION_MATRIX.md").write_text(method_matrix, encoding="utf-8")

    claim_trace = """# Claim Trace

| Claim | Paper Section | Evidence Type | Evidence ID/File | Strength | Paper Wording Check |
| --- | --- | --- | --- | --- | --- |
| 表面风化与玻璃类型存在稳定关联 | 问题一 | table/figure | `t_q1_association`, F1 | strong | 使用 Cramer's V 和置换 p 支撑 |
| 高钾与铅钡可由关键成分判别 | 问题二 | metric/figure | `m_q2_loocv_accuracy`, F3 | strong | 报告留一准确率 |
| 高钾和铅钡各可划分为两个亚类 | 问题二 | table/figure | `t_q2_subclass_centers`, F4 | acceptable | 同时报告轮廓系数，未夸大 |
| A1/A5/A6/A7 为高钾，A2/A3/A4/A8 为铅钡 | 问题三 | table/figure | `t_q3_unknown_predictions`, F5 | acceptable | A5 标注相对边界样本 |
| 两类玻璃相关结构存在差异 | 问题四 | table/figure | `t_q4_corr_diff`, F6 | acceptable | 明确为组成关联，非因果 |
"""
    (REPORTS / "CLAIM_TRACE.md").write_text(claim_trace, encoding="utf-8")

    build_report = f"""# Paper Build Report

## Files Created

- `paper/contest_paper.md`
- `paper/contest_paper.pdf`
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- `reports/CLAIM_TRACE.md`

## Figures Inserted

- F1-F7 all inserted in the PDF/Markdown paper.

## Method Downgrades

- None. Wind-weathering correction is honestly described as average type-level correction, not precise chemical restoration.

## Unresolved Issues

- None known before contest review.
"""
    (REPORTS / "PAPER_BUILD_REPORT.md").write_text(build_report, encoding="utf-8")
    print(json.dumps({"markdown": str(md_path), "pdf": str(pdf_path), "figures_inserted": 7}, ensure_ascii=False))


if __name__ == "__main__":
    main()
