from pathlib import Path
import shutil,json,sys,ast,hashlib
R=Path('revision_work_v4');repo=R/'ImmuneAging_Github';shutil.copytree('revision_work_v3/code_repo',repo,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
# Keep scientific source and figure generators together.
art=repo/'scripts/literature';art.mkdir(exist_ok=True)
for name in ['make_figures.py','collect_evidence.py','correct_metadata.py','fetch_core.py','resource_guide.py']:
 p=Path(r'F:\Ashley_Projects\ImmuneAging\script\BIB_review_workbench')/name
 if p.exists():shutil.copy2(p,art/name)
shutil.copy2('revision_work_v3/study_data.json',art/'study_data.json')
# The local package is one directory below the project root.
p=repo/'configs/default.json';cfg=json.loads(p.read_text());cfg.update(input_root='../data/benchmark_revision_500cells/processed',metadata_root='../data/benchmark_revision_500cells/metadata',reference_root='../tables/BIB_review_v2');p.write_text(json.dumps(cfg,indent=2))
for name in ['replay_secondary.py','plot_increment.py']:
 p=repo/'scripts'/name;s=p.read_text();s=s.replace('ROOT.parents[1]', 'ROOT.parent');p.write_text(s)
p=repo/'scripts/legacy/project_paths.json';s=p.read_text().replace('../../../../','../../../');p.write_text(s)
p=art/'make_figures.py';s=p.read_text(encoding='utf8');s=s.replace("'AIDA-based clocks; microglial featurisation preprint.'","'AIDA clocks resolve expression and cell proportions.'").replace("'sc-ImmuAging and siAge; mouse protein clock published online.'","'sc-ImmuAging, siAge and microglial featurisation.'").replace('Dates follow publication records; mouse study: online 2025, journal volume 2026. Microglia: preprint.','Selected publication milestones. Microglial featurisation: peer-reviewed study, 2025.')
p.write_text(s,encoding='utf8')
# Baseline AST fingerprints allow formatting-only edits to be checked.
fingerprints={str(p.relative_to(repo)):hashlib.sha256(ast.dump(ast.parse(p.read_text(encoding='utf-8-sig')),include_attributes=False).encode()).hexdigest() for p in repo.rglob('*.py')}
(R/'code_AST_before_format.json').write_text(json.dumps(fingerprints,indent=2))
print(len(fingerprints),'Python files staged')
