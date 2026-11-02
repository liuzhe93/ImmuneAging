import sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'revision_work/deps'))
sys.argv=['plot_transfer.py','--results',str(R.parent/'revision_work_v3/results'),'--output',str(R/'figures/main')]
runpy.run_path(str(R/'ImmuneAging_Github/scripts/plot_transfer.py'),run_name='__main__')
