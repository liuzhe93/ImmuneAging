from pathlib import Path
import subprocess
from PIL import Image,ImageOps,ImageDraw
R=Path('revision_work_v4/qa_render');exe=r'C:\Users\liuzh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
for pdf in R.glob('*.pdf'):
 out=R/pdf.stem;out.mkdir(exist_ok=True);subprocess.run([exe,'-scale-to','1400','-png',str(pdf),str(out/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 pages=sorted(out.glob('page-*.png'))
 for k in range(0,len(pages),6):
  sheet=Image.new('RGB',(1500,1950),'#cccccc');d=ImageDraw.Draw(sheet)
  for j,p in enumerate(pages[k:k+6]):
   im=Image.open(p);im.thumbnail((495,940));x=j%3*500;y=j//3*975;sheet.paste(im,(x,y+20));d.text((x+5,y+2),p.name,fill='black')
  sheet.save(R/(pdf.stem+f'_sheet{k//6+1}.jpg'))
print('Rendered all pages')
