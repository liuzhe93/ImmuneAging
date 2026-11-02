import sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'revision_work/deps'))
for name,flags in [('plot_transfer.py',['--results',str(R.parent/'revision_work_v3/results')]),('plot_increment.py',['--reference',str(R.parent/'revision_work_v2/results')])]:
 sys.argv=[name]+flags+['--output',str(R/'figures/main')];runpy.run_path(str(R/'ImmuneAging_Github/scripts'/name),run_name='__main__')
runpy.run_path(str(R/'ImmuneAging_Github/scripts/literature/make_figures.py'),run_name='__main__')
