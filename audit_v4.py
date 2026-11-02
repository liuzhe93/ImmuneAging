from pathlib import Path
import sys,json,re,csv,hashlib
sys.path.insert(0,'revision_work/deps')
import pandas as pd,numpy as np
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
R=Path('revision_work_v4');old=Path('revision_work_v2/results');new=Path('revision_work_v3/results');checks=[]
def check(name,value,details=''):
 if not value:raise AssertionError((name,details))
 checks.append({'check':name,'passed':bool(value),'details':details})
d=Document(R/'deliverables/Immune_ageing_BIB_review_v4.docx');text='\n'.join(p.text for p in d.paragraphs)
check('main_table_count',len(d.tables)==6)
# Verify every number in Table 5 against frozen metrics, including both interval bounds.
m=pd.read_csv(old/'metrics.csv');m=m[(m.n_cells==500)&(m.age_scope=='all')]
for row,model in zip(d.tables[4].rows[1:],['M0_median','M1_composition_EN','M1b_composition_Ridge','M1c_composition_HGB']):
 for cell,c in zip(row.cells[1:3],['aida','onek1k']):
  z=m[(m.model==model)&(m.evaluation=='OOF')&(m.test_cohort==c)].iloc[0]
  check('Table5 '+model+' '+c,all(f'{float(z[x]):.2f}' in cell.text for x in ['MAE','MAE_low','MAE_high']),cell.text)
 for src,dst in [('aida','onek1k'),('onek1k','aida')]:
  z=m[(m.model==model)&(m.evaluation=='external')&(m.train_cohort==src)&(m.test_cohort==dst)].iloc[0]
  check('Table5 external '+model+' '+src,all(f'{float(z[x]):.2f}' in row.cells[3].text for x in ['MAE','MAE_low','MAE_high']),row.cells[3].text)
# Source donor counts and nested eligibility used in Figure 1.
for c,expected in [('aida',{300:500,500:497,1000:476,3000:5}),('onek1k',{300:981,500:979,1000:802,3000:2})]:
 meta=pd.read_csv(Path('revision_work/data/processed')/f'{c}_donors.csv')
 for threshold,n in expected.items():check('Figure1 eligibility '+c+' '+str(threshold),int((meta.n_cells>=threshold).sum())==n,str(n))
 X=np.load(Path('revision_work/data/processed')/f'{c}_composition_500.npy')[meta.n_cells>=500];check('fraction closure '+c,np.max(abs(X.sum(1)-1))<1e-12)
# Figure 3 cells match fresh sensitivity fits and weighting outputs.
f=pd.read_csv(R/'figures/main/Figure_3_source.csv');metrics=pd.read_csv(new/'all_metrics.csv');weighted=pd.read_csv(new/'age_standardised_metrics.csv')
for row in f.itertuples():
 z=metrics if row.condition=='all' else weighted
 z=z[(z.representation==row.representation)&(z.train_cohort==row.train)&(z.test_cohort==row.test)&(z.model=='M1_composition_EN')]
 if row.condition=='all':z=z[z.training_age=='all'];col='MAE'
 else:z=z[(z.training_age==('common' if row.condition=='source_common' else 'all'))&(z.scheme=='five_year')];col='weighted_MAE'
 check('Figure3 '+row.representation+' '+row.condition+' '+row.train+' '+row.test,abs(row.MAE-float(z.iloc[0][col]))<1e-10)
# Resource summaries are medians of five recorded process repetitions, not newly measured end-to-end costs.
z=pd.read_csv(old/'resource_repeats.csv');s=pd.read_csv(old/'resource_summary.csv')
for row in s.itertuples():
 q=z[(z.cohort==row.cohort)&(z.model==row.model)&(z.training_donors==row.training_donors)]
 check('Figure4 repetitions '+row.cohort+' '+row.model+' '+str(row.training_donors),len(q)==5)
 for col in ['search_s','fit_s','predict_s','MAE','peak_process_RSS_MiB']:check('Figure4 median '+col+' '+str(row.Index),np.isclose(q[col].median(),getattr(row,col+'_median')))
# Fixed-donor depth results and stated improvements.
z=pd.read_csv(old/'matched_cell_predictions.csv');z['error']=abs(z.prediction-z.age);means=z.groupby(['cohort','n_cells']).error.mean()
for c,a,b,change in [('aida',8.63,7.96,.13),('onek1k',10.03,9.14,.10)]:
 check('Figure5 endpoints '+c,round(means[c,100],2)==a and round(means[c,1000],2)==b)
 check('Figure5 500-to-1000 '+c,round(means[c,500]-means[c,1000],2)==change)
# Figure6 donor-level paired source, arithmetic combination, and T control.
p=pd.read_csv(old/'deposited_paired_predictions.csv');check('Figure6 arithmetic mean',np.max(abs(p.combined-(p.expression+p.proportion)/2))<1e-10)
for c,n,values in [('aida',496,[8.68,9.73,8.67]),('onek1k',660,[17.23,28.31,22.50])]:
 q=p[(p.cohort==c)&(p.lineage=='CD14-positive monocyte')];check('Figure6 monocyte n '+c,len(q)==n)
 for name,value in zip(['proportion','expression','combined'],values):check('Figure6 MAE '+c+' '+name,round(abs(q[name]-q.age).mean(),2)==value)
t=pd.read_csv(new/'T_controls/T_control_summary.csv')
for c,n,delta in [('aida',497,2.12),('onek1k',979,2.90)]:
 q=t[(t.cohort==c)&(t.arm=='merged')].iloc[0];check('Figure6 merged T '+c,q.n==n and round(q.delta_MAE_vs_full17,2)==delta)
# No raster-only SVGs; all requested figure formats are present.
assets=[]
for folder,prefix,count in [('main','Figure_',6),('supplementary','Figure_S',8)]:
 root=R/'figures'/folder
 for i in range(1,count+1):
  stem=next(root.glob(prefix+str(i)+'_*.svg')).stem
  for ext in ['png','pdf','svg']:
   p=root/(stem+'.'+ext);check('figure export '+folder+' '+p.name,p.is_file() and p.stat().st_size>1000);assets.append({'figure':stem,'format':ext,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  tree=etree.parse(str(root/(stem+'.svg')));check('editable vector '+stem,len(tree.xpath('//*[local-name()="text"]'))>0 and not tree.xpath('//*[local-name()="image"]'))
# Three line rules, zero vertical/interior rules.
for i,t in enumerate(d.tables,1):
 for ri,row in enumerate(t.rows):
  for cell in row.cells:
   for border in cell._tc.xpath('./w:tcPr/w:tcBorders/*'):
    side=etree.QName(border).localname;on=border.get(qn('w:val'))=='single';expected=(ri==0 and side in ['top','bottom']) or (ri==len(t.rows)-1 and side=='bottom');check('Table border '+str(i)+' '+str(ri)+' '+side,on==expected)
# First numbered main figure and table mentions must be sequential, and occur before references.
pre=text.split('\nReferences\n')[0]
for kind in ['Figure','Table']:
 order=[]
 for match in re.finditer(r'(?<!Supplementary )\b'+kind+r' ([1-6])\b',pre):
  n=int(match[1])
  if n not in order:order.append(n)
 check(kind+' first-mention order',order==[1,2,3,4,5,6],str(order))
check('references follow all main figures',text.index('References')>text.index('Figure 6 Paired'))
final=pd.read_csv(R/'references_final.csv');check('65 unique DOI references',len(final)==65 and final.doi.str.lower().nunique()==65)
check('reference count within requested limits',30<len(final)<100)
check('published microglia version',final.loc[final.key=='microglia','doi'].iloc[0]=='10.1111/acel.70095')
(R/'figure_asset_manifest.json').write_text(json.dumps(assets,indent=2))
(R/'quantitative_and_structure_checks.json').write_text(json.dumps({'checks':len(checks),'all_passed':True,'records':checks},indent=2))
print('Passed',len(checks),'numeric and structural checks; 42 figure assets')
