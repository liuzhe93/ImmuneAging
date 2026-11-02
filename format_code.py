from pathlib import Path
import sys,json,ast,hashlib,shutil
R=Path('revision_work_v4');repo=R/'ImmuneAging_Github';shutil.copy2(R/'references_verified.json',repo/'scripts/literature/references_verified.json')
sys.path.insert(0,str(R/'formatting_deps'));import black
before={};after={}
for p in repo.rglob('*.py'):
 s=p.read_text(encoding='utf-8-sig');before[str(p.relative_to(repo))]=ast.dump(ast.parse(s),include_attributes=False)
 try:result=black.format_file_contents(s,fast=False,mode=black.FileMode(line_length=88))
 except black.NothingChanged:result=s
 p.write_text(result,encoding='utf8');after[str(p.relative_to(repo))]=ast.dump(ast.parse(result),include_attributes=False)
assert before==after
(R/'code_format_check.json').write_text(json.dumps({'python_files':len(after),'AST_unchanged_by_formatting':True,'formatter':'Black '+black.__version__},indent=2))
(R/'replay_cleaned_code.py').write_text('''import sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'revision_work/deps'))
sys.argv=['run_reproduction.py','--input',str(R.parent/'revision_work/data/processed'),'--metadata',str(R.parent/'revision_work/evidence'),'--reference',str(R.parent/'revision_work_v2/results'),'--output',str(R/'replay_results')]
runpy.run_path(str(R/'ImmuneAging_Github/scripts/run_reproduction.py'),run_name='__main__')
''',encoding='utf8')
print('Formatted',len(after),'files; AST unchanged')
