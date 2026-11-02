from pathlib import Path
import sys,importlib.metadata as im,json
R=Path('revision_work_v4');repo=R/'ImmuneAging_Github';p=repo/'requirements.txt';s=p.read_text(encoding='utf8')
for name in ['reportlab','lxml']:
 if not any(line.startswith(name+'==') for line in s.splitlines()):s+=name+'=='+im.version(name)+'\n'
p.write_text(s,encoding='utf8')
# Format the final plotting change without launching worker processes.
sys.path.insert(0,str(R/'formatting_deps'));import black
p=repo/'scripts/plot_transfer.py'
try:s=black.format_file_contents(p.read_text(encoding='utf8'),fast=False,mode=black.FileMode())
except black.NothingChanged:s=p.read_text(encoding='utf8')
p.write_text(s,encoding='utf8')
# Update the conceptual generator's bibliography and verify its full execution.
