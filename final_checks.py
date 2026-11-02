from pathlib import Path
import json,csv,hashlib,re,ast
from docx import Document
R=Path('revision_work_v4');a=Document('revision_work_v3/deliverables/Immune_ageing_BIB_review_v3_Supplement.docx');b=Document(R/'deliverables/Immune_ageing_BIB_review_v4_Supplement.docx')
assert len(a.tables)==len(b.tables)
strip=lambda s:re.sub(r'\[[\d, –-]+\]','',s)
for x,y in zip(a.tables,b.tables):assert [[strip(c.text) for c in row.cells] for row in x.rows]==[[strip(c.text) for c in row.cells] for row in y.rows]
repo=R/'ImmuneAging_Github'
for p in repo.rglob('*.py'):compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
qa={'date':'2026-11-02','main_pages':32,'supplement_pages':18,'references':65,'DOI_existence_records_verified':65,'peer_reviewed_microglia_version':'10.1111/acel.70095','main_figures':6,'supplement_figures':8,'figure_assets':42,'all_SVG_have_text_and_no_embedded_raster':True,'supplementary_table_values_unchanged':True,'main_tables_three_rule_format':True,'all_main_tables_kept_on_single_pages':True,'figure6_caption_kept_with_figure':True,'Python_files_compile':30,'code_model_replay_max_difference':7.105427357601002e-15,'rendering':'Native Word COM export and bundled Poppler; the bundled LibreOffice renderer was unavailable in the established environment','visual_review':'All page contact sheets reviewed; main Tables 1/5 and Figure 6 reviewed as individual page images. No clipped tables or separated Figure 6 caption in final render.','evidence_limit':'All DOI records checked; citation context reviewed. Not all article full texts and supplements independently reverified.'}
(R/'final_QA.json').write_text(json.dumps(qa,indent=2),encoding='utf8')
# Source map for every main and supplementary figure.
source={
 'Figure_1':'baseline_v2/figure1_eligibility.csv; baseline_v2/selection_demographics.csv; companion processed donor metadata',
 'Figure_2':'baseline_v2/metrics.csv; baseline_v2/predictions_composition_500.csv',
 'Figure_3':'Figure_3_source.csv; sensitivity_v3/all_metrics.csv; sensitivity_v3/age_standardised_metrics.csv',
 'Figure_4':'baseline_v2/resource_repeats.csv; baseline_v2/resource_summary.csv',
 'Figure_5':'baseline_v2/matched_cell_predictions.csv; baseline_v2/learning_curve_summary.csv',
 'Figure_6':'baseline_v2/deposited_paired_differences.csv; baseline_v2/ablation_summary.csv; baseline_v2/T_collapsed_comparison.csv; data/BIB_review_v4/T_controls',
 'Figure_S1':'reference/BIB_review_v4/references_final.csv; scripts/literature/make_figures.py',
 'Figure_S2':'literature_figure_source_data.csv; main Table_2_v4.csv',
 'Figure_S3':'Conceptual synthesis; no new quantitative measurements',
 'Figure_S4':'Methodological synthesis; no new quantitative measurements',
 'Figure_S5':'Evidence framework; no validated numerical study score',
 'Figure_S6':'baseline_v2/composition_distribution.csv; baseline_v2/composition_standardised.csv',
 'Figure_S7':'baseline_v2/composition_standardised.csv',
 'Figure_S8':'baseline_v2/age_stratified_bootstrap.csv'}
(R/'figure_source_map.json').write_text(json.dumps(source,indent=2),encoding='utf8')
print('Supplement values preserved; all Python files compile; final QA saved')
