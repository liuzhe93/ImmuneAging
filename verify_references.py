import json,requests,time,concurrent.futures,re,sys
from pathlib import Path
R=Path(__file__).resolve().parent;sys.stdout.reconfigure(encoding='utf8');refs=json.loads((R.parent/'revision_work_v3/references_verified.json').read_text(encoding='utf8'))
def one(item):
 k,v=item
 if not v.get('verified'):return None
 doi=v['record']['doi'];out={'key':k,'doi':doi,'checked_date':'2026-11-02'}
 for name,url in [('crossref','https://api.crossref.org/works/'+doi),('europepmc','https://www.ebi.ac.uk/europepmc/webservices/rest/search')]:
  try:
   q=requests.get(url,params={'query':'DOI:'+doi,'format':'json','resultType':'core'} if name=='europepmc' else None,timeout=35);out[name+'_status']=q.status_code
   if q.ok:out[name]=q.json()
  except Exception as e:out[name+'_error']=str(e)
 print(k,out.get('crossref_status'),out.get('europepmc_status'),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:out=[v for v in ex.map(one,refs.items()) if v]
(R/'reference_checks_raw.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified records',len(out))
