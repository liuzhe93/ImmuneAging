from pathlib import Path
import json,csv,html,re
R=Path('revision_work_v4');p=R/'citation_placement_audit.csv';rows=list(csv.DictReader(p.open(encoding='utf-8-sig')));full={'aida_clock','ideal','mouse','omniage','prior_review','repertoire','scimmu','siage','tictock','zhu','microglia'}
for row in rows:row['evidence_level']='Indexed record plus archived primary full text' if row['key'] in full else 'Indexed record and abstract; not a complete full-text audit'
with p.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
repo=R/'ImmuneAging_Github';p=repo/'.gitignore';p.write_text(p.read_text(encoding='utf8')+'scripts/literature/figures/\nscripts/literature/figure_source_data.csv\n',encoding='utf8')
p=repo/'docs/DATA_AND_PROVENANCE.md';s=p.read_text(encoding='utf8').replace('No licence has been fabricated.','');p.write_text(s,encoding='utf8')
# Keep the bibliography behind the figure generator consistent with the final manuscript.
p=repo/'scripts/literature/references_verified.json';z=json.loads(p.read_text(encoding='utf8'));p.write_text(json.dumps({k:v for k,v in z.items() if v.get('verified')},ensure_ascii=False,indent=2),encoding='utf8')
p=repo/'scripts/literature/study_data.json';s=p.read_text(encoding='utf8').replace('Microglia preprint','Microglia clock').replace('Microglia evidence is a preprint.','Microglia evidence is from the peer-reviewed 2025 study.');p.write_text(s,encoding='utf8')
# Word table extracts carry the final citation numbering.
from docx import Document
d=Document(R/'deliverables/Immune_ageing_BIB_review_v4.docx');out=R/'table_sources';out.mkdir(exist_ok=True)
for i,t in enumerate(d.tables,1):
 with (out/f'Table_{i}_v4.csv').open('w',newline='',encoding='utf-8-sig') as f:csv.writer(f).writerows([[c.text for c in row.cells] for row in t.rows])
refs=json.loads((R/'references_verified.json').read_text(encoding='utf8'));order=json.loads((R/'reference_numbers_v4.json').read_text(encoding='utf8'));bib=[];ris=[]
for key in order:
 rec=refs[key]['record'];title=html.unescape(re.sub('<[^>]+>','',rec['title']));year=2026 if key=='mouse' else rec.get('journalInfo',{}).get('yearOfPublication') or rec.get('pubYear');authors=[a.get('fullName') or a.get('collectiveName','') for a in rec.get('authorList',{}).get('author',[])]
 bib.append('@article{'+key+',\n title = {'+title+'},\n author = {'+' and '.join(authors)+'},\n year = {'+str(year)+'},\n doi = {'+rec['doi']+'}\n}')
 ris.append('TY  - JOUR\nTI  - '+title+'\nPY  - '+str(year)+'\nDO  - '+rec['doi']+'\n'+''.join('AU  - '+a+'\n' for a in authors)+'ER  - \n')
(R/'references_v4.bib').write_text('\n\n'.join(bib),encoding='utf8');(R/'references_v4.ris').write_text('\n'.join(ris),encoding='utf8')
print('Saved final citations, table sources and bibliography exports')
