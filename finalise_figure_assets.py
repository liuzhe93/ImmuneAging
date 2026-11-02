from pathlib import Path
import shutil,subprocess
R=Path('revision_work_v4');src=R/'ImmuneAging_Github/scripts/literature/figures';dst=R/'figures/supplementary'
for ext in ['pdf','svg']:shutil.copy2(src/('Figure_1_milestones.'+ext),dst/('Figure_S1_milestones.'+ext))
exe=r'C:\Users\liuzh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
subprocess.run([exe,'-singlefile','-scale-to','2400','-png',str(dst/'Figure_S1_milestones.pdf'),str(dst/'Figure_S1_milestones')],check=True)
