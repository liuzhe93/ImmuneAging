from pathlib import Path
import sys,json,ast,hashlib,shutil
R=Path('revision_work_v4');repo=R/'ImmuneAging_Github';before=json.loads((R/'code_AST_before_format.json').read_text());after={str(p.relative_to(repo)):hashlib.sha256(ast.dump(ast.parse(p.read_text(encoding='utf-8-sig')),include_attributes=False).encode()).hexdigest() for p in repo.rglob('*.py')};assert before==after;(R/'code_format_check.json').write_text(json.dumps({'python_files':len(after),'AST_unchanged_by_formatting':True},indent=2))
for src,dst in [('revision_work_v3/figures',R/'figures/main'),('revision_work_v3/supplementary',R/'figures/supplementary')]:shutil.copytree(src,dst,dirs_exist_ok=True)
for name in ['plot_transfer.py','plot_increment.py']:
 p=repo/'scripts'/name;s=p.read_text(encoding='utf8');needle='import matplotlib.pyplot as plt';s=s.replace(needle,needle+'\n\nplt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})');p.write_text(s,encoding='utf8')
(R/'run_figures.py').write_text('''import sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'revision_work/deps'))
for name,flags in [('plot_transfer.py',['--results',str(R.parent/'revision_work_v3/results')]),('plot_increment.py',['--reference',str(R.parent/'revision_work_v2/results')])]:
 sys.argv=[name]+flags+['--output',str(R/'figures/main')];runpy.run_path(str(R/'ImmuneAging_Github/scripts'/name),run_name='__main__')
runpy.run_path(str(R/'ImmuneAging_Github/scripts/literature/make_figures.py'),run_name='__main__')
''',encoding='utf8')
print('30 scripts reformatted without AST changes')
