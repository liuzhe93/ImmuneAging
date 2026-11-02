from pathlib import Path
import json,csv,sys,shutil,re,ast,hashlib
R=Path('revision_work_v4');repo=R/'ImmuneAging_Github';final=list(csv.DictReader((R/'references_final.csv').open(encoding='utf-8-sig')));raw=json.loads((R/'reference_checks_raw.json').read_text(encoding='utf8'));bykey={x['key']:x for x in raw};refs=json.loads((R/'references_verified.json').read_text(encoding='utf8'))
old=R/'reference_existence_audit.csv';shutil.copy2(old,R/'reference_existence_initial_v3_audit.csv');rows=[]
for row in final:
 k=row['key'];r=refs[k]['record'];rows.append({'number':row['number'],'key':k,'doi':r['doi'],'title':r['title'],'year_as_cited':row['year'],'existence':'verified exact DOI in Europe PMC; Crossref cross-check where available','record_id':r.get('id'),'source':r.get('source'),'evidence_url':'https://europepmc.org/article/'+r.get('source','')+'/'+r.get('id',''),'checked_date':'2026-11-02','note':'Replaces 2024 preprint with peer-reviewed 2025 report' if k=='microglia' else 'Online metadata: 2025; publisher PDF volume imprint: 2026; retain volume-year citation' if k=='mouse' else ''})
with old.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Make evidence level explicit for the citation audit instead of conflating existence and full-text support.
p=R/'citation_placement_audit.csv';placements=list(csv.DictReader(p.open(encoding='utf-8-sig')))
full={'aida_clock','ideal','mouse','omniage','prior_review','repertoire','scimmu','siage','tictock','zhu','microglia'}
methods={'integration','scvi','harmony','seurat','pseudorep','donor','sccoda','dream','batch','cv','small_samples','leakage','bias_age','shap','interpretable','tripod','probast','fair','benchmark','clinical','surrogate','foundation','scgpt'}
for row in placements:
 k=row['key'];row['evidence_level']='Indexed record plus archived primary full text' if k in full else 'Indexed record and abstract; primary-report role checked; not a complete full-text audit'
 row['review']='Supports the named study methods/counts; predictions retain their original cohort role.' if k in full else 'Supports the stated methodological principle; does not constitute new immune-age performance evidence.' if k in methods else 'Supports the named biological result or biomarker context; no cross-study accuracy ranking is inferred.'
with p.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(placements[0]));w.writeheader();w.writerows(placements)
(repo/'README.md').write_text('''# Immune ageing clocks

Analysis code for an adult PBMC case study accompanying a critical review of immune ageing clocks. The primary benchmark compares cell-composition models in OneK1K and AIDA. A separate analysis evaluates predictions released by the authors of a transcriptomic clock.

## Setup

Use Python 3.12 in an isolated environment:

```powershell
python -m pip install -r requirements.txt
python scripts/run_reproduction.py --demo --output outputs/demo
```

The demo uses synthetic data and is only an installation check.

## Reproduce the case study

Place this folder at `ImmuneAging/ImmuneAging_Github`. The default configuration expects the companion project folders `../data/benchmark_revision_500cells` and `../tables/BIB_review_v2`. Edit `configs/default.json` or pass `--input`, `--metadata`, `--reference` and `--output` when relocating the inputs.

```powershell
python scripts/run_reproduction.py
python scripts/replay_secondary.py
python scripts/plot_transfer.py
python scripts/plot_increment.py
```

The primary entry refits median, elastic-net, ridge and gradient-boosting models under donor-level nested validation. It also runs shared-label, source-age, age-weighting and T-cell controls. The main threshold is 500 retained cells per donor; the earlier 300/1000 eligibility analyses are in `scripts/legacy`. Recorded primary replay times were approximately 35–110 seconds on one CPU thread, excluding downloads. Actual times depend on the machine and disk.

## Repository structure

- `src/immune_ageing`: model fitting, donor summaries, age weighting and mapping audits.
- `scripts`: tested primary entry, released-prediction aggregation and Figure 3/6 plotting.
- `scripts/legacy`: acquisition, sampling, earlier robustness and resource analyses, and the original quantitative figure scripts.
- `scripts/literature`: literature metadata and conceptual figure generators; `make_figures.py` writes vector PDF/SVG files.
- `configs`: portable input paths and fixed analysis settings.
- `reproduction`: aggregate expected results, checksums and acceptance records.
- `docs`: input fields, data sources and analysis boundaries.

Legacy scripts preserve the original analysis workflow and may require their recorded inputs and execution order. A separate implementation reproduced 11,808 primary prediction rows within 1e-8. This is a computational check within the project, not replication by an independent research group.

## Interpretation

Five shared cell groups are renormalised after residual Other cells are excluded from each sampled set; this does not establish biological annotation equivalence. Bootstrap intervals use fixed donor predictions and omit refitting uncertainty. Released expression predictions retain the original authors' training and sampling procedures. No newly trained expression, joint-input or pretrained-model results are included.

## Data and release

Scientific donor-level inputs, models and generated outputs are excluded from this repository. Obtain source data under the terms documented in `docs/DATA_AND_PROVENANCE.md`; public access alone does not establish redistribution permission. A software licence should be selected by the authors before public release. This local package has not been uploaded to GitHub.
''',encoding='utf8')
shutil.copy2(R/'replay_results/acceptance_report.json',repo/'reproduction/v4_cleaned_code_acceptance.json')
shutil.copy2(R/'code_format_check.json',repo/'reproduction/code_format_check.json')
shutil.copy2(R/'reference_existence_audit.csv',repo/'reproduction/reference_existence_audit.csv')
# Record all provided assets and their limitations for Illustrator editing.
(R/'figures/README_Illustrator.md').write_text('''# 图件编辑说明

main 为6张主图；supplementary 为8张附图。每张图均提供PNG、PDF和SVG，共42个文件。PNG用于预览；PDF/SVG保留矢量线条、点、色块和文字，可在Adobe Illustrator中编辑。图3热图已改用矢量矩形，避免把色块嵌入为位图。所有SVG已检查包含文字节点且无嵌入位图。

这些文件是矢量成图，不是分层AI源文件；Illustrator可能需要取消编组，且本机缺少字体时会提示替换。SVG保留文字便于统一字体，PDF字体嵌入方式可能影响文字编辑。修改字体或尺寸后请再次核对图例、坐标与数值。完整图件校验和见figure_asset_manifest.json。
''',encoding='utf8')
# A record of changes, without overstating full-text or completeness checks.
recent=sum(int(x['year'])>=2024 for x in final)
(R/'BIB_review_v4_核查报告.md').write_text(f'''# 第四版修改与核查记录

依据用户上传的v3继续修改，保留其摘要、引言及主要行文调整。主分析500细胞、300/1000敏感性设定未改变。

## 文献与引用

正文现有65条参考文献，均匹配到真实的Europe PMC精确DOI记录，另保存Crossref查询结果。2024—2026年的文献共{recent}条。保留Hannum、Horvath、IMM-AGE、iAge、PhenoAge、GrimAge、DunedinPACE等基础研究，补充Peters 2015血液转录组、Lehallier 2019血浆蛋白组和Oh 2023器官蛋白组研究，使相关论述有直接来源。

发现并改正：小胶质细胞时钟已有正式版本，改引Stanley等2025年Aging Cell，DOI 10.1111/acel.70095，替换旧预印本，并同步修改正文、表1和图S1。鼠免疫时钟的在线记录为2025、出版社PDF卷年为2026，保留2026;17:640并记录差异，没有把两个年份当成两篇论文。

逐段审阅引用位置，将免疫细胞变化、动物因果证据、模型任务与验证原则分别挂接到对应来源。重新按正文及内嵌图表首次出现顺序编号。reference_existence_audit.csv记录每条DOI及来源；citation_placement_audit.csv记录引用上下文与证据层级。真实性核验不等同于每篇完整方法和全部补充材料均经独立复核：11篇有归档全文证据，其余主要依据索引、摘要及其实际引用角色。此次为聚焦叙述综述，不能保证引用了领域全部经典或近期文章。

## 正文与图表

六张主图和六张主表已移至相关正文之后；主图、主表的首次出现顺序均为1至6，参考文献置于正文和主图表之后。所有正文和补充材料内的Word表格改为三线表：表顶线、表头下线、表底线，无竖线及内部网格线。图3与图6重新导出；图S1更新正式发表年份和表述。

逐项复核表5全部模型MAE及区间，图1供者资格，图3矩阵数值，图4五次进程重复及中位数，图5固定供者深度结果，图6预测均值和T对照。数值与结构检查共1128项通过。这些检查针对现有冻结输入和结果，不表示新增原始表达实验、功能验证或独立研究者复现。文献中的定量条目另与归档原文、索引摘要和来源记录核对。

## 文字与代码

逐段逐句检查上传稿，修正不完整标题、缺失空格、重复的T对照描述及混合拼写；保留方法边界和必要的不确定性。专业可读性调整不等于承诺通过任何AI文本检测，也不删除实际使用披露。作者仍需核实最终科学表述和投稿声明。

30个Python文件统一为可读的缩进和分行格式，格式化前后AST一致；路径调整适配ImmuneAging_Github目录，图3色块改为可编辑矢量对象。整理后实际重跑核心模型，11808条预测最大差异7.1e-15，低于1e-8容差；未改变科学模型参数或结果。代码目录含依赖、配置、来源说明、合成演示、脚本和验收记录，尚未上传GitHub。

## 交付位置

正文与补充Word：F:/Ashley_Projects/ImmuneAging/manuscript/
图件：F:/Ashley_Projects/ImmuneAging/figures/BIB_review_v4/，共14张图，每张PNG/PDF/SVG。
代码：F:/Ashley_Projects/ImmuneAging/ImmuneAging_Github/
文献及引用核查：F:/Ashley_Projects/ImmuneAging/reference/BIB_review_v4/
数值验收：F:/Ashley_Projects/ImmuneAging/logs/BIB_review_v4/
''',encoding='utf8')
print('Reference years >=2024:',recent,'of',len(final))
