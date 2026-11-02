from pathlib import Path
import shutil,json,hashlib
R=Path(__file__).resolve().parent;B=Path(r'F:\Ashley_Projects\ImmuneAging')
M=B/'manuscript';M.mkdir(parents=True,exist_ok=True)
for name in ['Immune_ageing_BIB_review_v4.docx','Immune_ageing_BIB_review_v4_Supplement.docx']:shutil.copy2(R/'deliverables'/name,M/name)
shutil.copy2(R/'BIB_review_v4_核查报告.md',M/'BIB_review_v4_核查报告.md')
G=B/'ImmuneAging_Github';shutil.copytree(R/'ImmuneAging_Github',G,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs','figures','figure_source_data.csv'))
F=B/'figures'/'BIB_review_v4';shutil.copytree(R/'figures',F,dirs_exist_ok=True)
for name in ['figure_asset_manifest.json','figure_source_map.json']:shutil.copy2(R/name,F/name)
REF=B/'reference'/'BIB_review_v4';REF.mkdir(parents=True,exist_ok=True)
for name in ['reference_checks_raw.json','microglia_published_record.json','reference_existence_audit.csv','citation_placement_audit.csv','references_final.csv','reference_numbers_v4.json','references_v4.bib','references_v4.ris','references_verified.json','quantitative_literature_evidence.json']:shutil.copy2(R/name,REF/name)
shutil.copytree(R/'evidence',REF/'source_evidence',dirs_exist_ok=True)
shutil.copy2(R/'source_v3.docx',REF/'user_uploaded_v3.docx')
T=B/'tables'/'BIB_review_v4';shutil.copytree(R/'table_sources',T,dirs_exist_ok=True)
shutil.copytree(R.parent/'revision_work_v2/results',T/'baseline_v2',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.joblib','*.npz'))
shutil.copytree(R.parent/'revision_work_v3/results',T/'sensitivity_v3',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.joblib','*.npz'))
shutil.copy2(R/'figures/main/Figure_3_source.csv',T/'Figure_3_source.csv')
shutil.copy2(R/'ImmuneAging_Github/scripts/literature/figure_source_data.csv',T/'literature_figure_source_data.csv')
shutil.copytree(R/'replay_results',B/'data'/'BIB_review_v4',dirs_exist_ok=True)
S=B/'script'/'BIB_review_v4';S.mkdir(parents=True,exist_ok=True)
for p in R.glob('*.py'):shutil.copy2(p,S/p.name)
# Preserve the authoring scripts as a provenance snapshot, separate from the runnable analysis package.
(S/'README.md').write_text('Authoring and verification workflow snapshot. Scientific analysis and figure-generation entry points are in ../../ImmuneAging_Github. Document builders retain paths to the staged source documents and earlier revision inputs used during editing; adapt those paths before rebuilding documents outside the staging workspace. The source v3 document and verified bibliography are retained in ../../reference/BIB_review_v4.\n',encoding='utf8')
L=B/'logs'/'BIB_review_v4';L.mkdir(parents=True,exist_ok=True)
for name in ['final_QA.json','quantitative_and_structure_checks.json','code_format_check.json','figure_asset_manifest.json']:shutil.copy2(R/name,L/name)
shutil.copy2(R/'replay_results/acceptance_report.json',L/'cleaned_code_acceptance.json')
# A compact inventory validates the delivered files without altering earlier revisions.
manifest=[]
roots=[G,F,REF,T,B/'data'/'BIB_review_v4',S,L]
for root in roots:
 for p in root.rglob('*'):
  if p.is_file():manifest.append({'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for p in [M/'Immune_ageing_BIB_review_v4.docx',M/'Immune_ageing_BIB_review_v4_Supplement.docx',M/'BIB_review_v4_核查报告.md']:manifest.append({'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(L/'archive_sha256.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('Archived',len(manifest),'files. Code:',G)
