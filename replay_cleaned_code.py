import sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'revision_work/deps'))
sys.argv=['run_reproduction.py','--input',str(R.parent/'revision_work/data/processed'),'--metadata',str(R.parent/'revision_work/evidence'),'--reference',str(R.parent/'revision_work_v2/results'),'--output',str(R/'replay_results')]
runpy.run_path(str(R/'ImmuneAging_Github/scripts/run_reproduction.py'),run_name='__main__')
