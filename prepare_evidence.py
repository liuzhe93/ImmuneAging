from pathlib import Path
import json,re,csv,html,shutil,sys
from lxml import etree
R=Path('revision_work_v4');V=Path('revision_work_v3');refs=json.loads((V/'references_verified.json').read_text(encoding='utf8'));raw=json.loads((R/'reference_checks_raw.json').read_text(encoding='utf8'));records={x['key']:x for x in raw}
# Save primary full-text evidence already used to extract the reported study counts.
D=R/'evidence';D.mkdir(exist_ok=True)
for p in Path(r'F:\Ashley_Projects\ImmuneAging\script\BIB_review_workbench\fulltext').glob('*.xml'):shutil.copy2(p,D/p.name)
ledger=[]
for p in D.glob('*.xml'):
 tree=etree.parse(str(p));paras=tree.xpath('//p')
 for i,par in enumerate(paras,1):
  text=' '.join(''.join(par.itertext()).split())
  if any(t in text for t in ['1,081','1081','0.9940','0.8894','3,501','3501','1,058,909','1,284','2,609','103 features','103 molecular','500 donors','784','122','CMUCH']):ledger.append({'source':p.name,'paragraph':i,'xpath':tree.getpath(par),'text_for_internal_check':text})
(R/'quantitative_literature_evidence.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf8')
rows=[]
for k,v in refs.items():
 if not v.get('verified'):continue
 r=records[k];ep=r.get('europepmc',{}).get('resultList',{}).get('result',[]);match=[a for a in ep if a.get('doi','').lower()==v['record']['doi'].lower()];assert len(match)==1,(k,match);a=match[0]
 norm=lambda t:re.sub('[^a-z0-9]','',html.unescape(re.sub('<[^>]+>','',t)).lower())
 old=norm(v['record']['title']);new=norm(a['title']);rows.append({'key':k,'doi':a['doi'],'title':html.unescape(re.sub('<[^>]+>','',a['title'])),'original_title_exact_normalised_match':old==new,'year_indexed':a.get('pubYear'),'journal_year':a.get('journalInfo',{}).get('yearOfPublication'),'PMID_or_record_id':a.get('id'),'source':a.get('source'),'Crossref_HTTP':r.get('crossref_status'),'Europe_PMC_DOI_match':True,'existence_status':'verified','article_status':'preprint' if k=='microglia' else 'journal record','evidence_url':'https://europepmc.org/article/'+a.get('source','')+'/'+a.get('id',''),'checked_date':'2026-11-02'})
 # Bibliography uses freshly retrieved indexed records, not generated titles.
 v['record']=a
(R/'references_verified.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf8')
with (R/'reference_existence_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('All',len(rows),'DOIs matched exact indexed records; title mismatches:',[x['key'] for x in rows if not x['original_title_exact_normalised_match']])
print('\n'.join(x['key']+' '+str(x['year_indexed'])+' / '+str(x['journal_year']) for x in rows if x['key'] in ['mouse','buckley','dream','microglia']))
print('Evidence hits',len(ledger))
