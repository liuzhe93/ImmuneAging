from pathlib import Path
import json,csv,re,html,copy,sys
from collections import Counter
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parent;V=R.parent/'revision_work_v3';OUT=R/'deliverables';OUT.mkdir(exist_ok=True)
refs=json.loads((R/'references_verified.json').read_text(encoding='utf8'))
old=list(csv.DictReader((V/'deliverables/reference_verification.csv').open(encoding='utf-8-sig')));keymap={int(x['number']):x['key'] for x in old};keymap.update({63:'proteome',64:'organ',65:'peters'})
DOC=Document(R/'source_v3.docx');paras=DOC.paragraphs;anchors={i:p for i,p in enumerate(paras)}
# Preserve the uploaded revision; edit only the passages identified during the audit.
changes={
 22:'Immune ageing involves changes in haematopoiesis, thymic output, lymphocyte differentiation, innate sensing and inflammatory signalling, modified by chronic antigen exposure and metabolic context [2, 17]. Experiments in mice show that an aged immune compartment can contribute to dysfunction in other organs [18, 19]. These findings motivate the study of immune ageing beyond chronological-age prediction, but do not establish that every blood-derived age predictor measures the relevant causal processes.',
 25:'3.2 Cell composition and within-lineage molecular state',
 33:'ipAGE provides an example of inflammatory age prediction in a clinical setting. The study included 83 controls and 76 participants with end-stage renal disease and used elastic net to construct a protein-based predictor [11]. The total clinical cohort should be distinguished from the controls used to establish the age relationship. In kidney disease, altered inflammation and protein clearance can affect the score, so an elevated prediction requires disease-specific interpretation.',
 46:'Stanley and colleagues compared cell-frequency features, landmark kernel representations and pseudobulk strategies in microglial datasets covering mouse ageing and human fetal development [16]. Their peer-reviewed study showed that the choice of aggregation affects clock performance and that simple summaries can retain useful predictive information. These datasets answer different biological questions and should not be pooled into one human age scale. Work in neurogenic regions and single-cell methylation provides further context for cell-resolved age estimation [32, 33].',
 61:'Pretrained representations require the same matched comparisons. Frozen encoders followed by supervised age-prediction models should be distinguished from fine-tuned encoders, and overlap between pretraining and evaluation data should be documented. scGPT provides one approach to learning representations from single-cell profiles [50]. A separate zero-shot evaluation found limitations in several single-cell foundation-model tasks [51]; that result does not establish their performance in donor-level immune age prediction. Training an age-prediction model on frozen embeddings uses age labels and is not zero-shot age prediction.',
 91:'Two additional controls tested the information in T-cell subtype proportions (Figure 6B). The 17 fractions sum to one, so deleting eight T-lineage columns without renormalising the remaining features retains total T-cell abundance implicitly. This nine-feature control increased MAE by 2.12 years in AIDA and 2.90 years in OneK1K. A ten-feature control instead merged the eight T-cell subsets into one total-T fraction and retained the non-T features. Under the same nested evaluation, the merging control increased MAE by 2.12 years in AIDA (95% bootstrap interval, 1.60–2.62) and 2.90 years in OneK1K (2.38–3.39). Thus, subtype proportions contributed predictive information in these models. Although the two controls had similar rounded MAEs, their donor predictions differed by up to 0.174 years in AIDA and 1.088 years in OneK1K. Adding a redundant total-T feature changes the penalised parameterisation. Separate inputs, fold parameters, coefficients and predictions are provided with Supplementary Table S18. These comparisons do not establish causal effects of T-cell subsets on ageing.'
}
for i,s in changes.items():anchors[i].text=s
anchors[16].text+=' Table 1 summarises the measurements and modelling approaches reviewed here. Supplementary Figures S1–S5 show selected milestones, cohort sizes, biological representations, validation designs and levels of evidence.'
anchors[18].text=anchors[18].text.replace('29 October 2026','2 November 2026')
anchors[19].text=anchors[19].text.replace('The microglial featurisation study is explicitly treated as a preprint, and its mixed developmental and ageing datasets are considered separately from adult human blood [16].','The microglial study is cited in its peer-reviewed 2025 version; its developmental and ageing datasets are considered separately from adult human blood [16].')
anchors[32].text+=' Plasma-proteome studies have documented age-related trajectories and organ-associated signals, supporting the need to distinguish circulating protein age from immune-specific ageing [63, 64].'
anchors[36].text='Earlier work established age-associated transcriptional signatures in human peripheral blood [65]. '+anchors[36].text
anchors[58].text='5.3 Model comparison and biological interpretation'
anchors[59].text+=' Table 3 summarises what the main validation designs can establish.'
anchors[63].text+=' Table 4 lists the information needed to reproduce model development and reuse a fitted predictor.'
anchors[82].text=anchors[82].text.replace('comparisons.With','comparisons. With')
anchors[108].text+=' Table 6 relates the available evidence to intended research and clinical settings; clinical use also requires evaluation of added benefit within the relevant care pathway [62].'
# Capture existing table/figure blocks before removing their old end placement.
tables={};figures={}
for p in paras:
 m=re.match(r'Table ([1-6]) ',p.text)
 if m:
  t=p._p.getnext();tables[int(m[1])]=[p._p,t,t.getnext()]
 m=re.match(r'Figure ([1-6]) ',p.text)
 if m:
  image=p._p.getnext();figures[int(m[1])]=[image,p._p,image.getnext()]
body=DOC._element.body;start=paras[115]._p
for el in list(body)[list(body).index(start):]:
 if el.tag!=qn('w:sectPr'):body.remove(el)
# Restore a consistent heading hierarchy and UK spelling outside cited titles.
for i,p in anchors.items():
 if i>=115:continue
 if i in [29,49,64,94,106,110,113]:p.style='Heading 1'
 elif re.match(r'\d+\.\d+\s',p.text):p.style='Heading 2';p.text=re.sub(r'^(\d+\.\d+)\s+',r'\1 ',p.text)
 if p.style.name=='Heading 1':p.paragraph_format.page_break_before=False
 s=p.text
 for a,b in [('aging','ageing'),('modeling','modelling'),('analyzed','analysed'),('reanalyzed','reanalysed'),('regularized','regularised'),('renormalized','renormalised'),('recognized','recognised'),('summarizes','summarises'),('summarize','summarise'),('center','centre'),('tumor','tumour'),('hematopoiesis','haematopoiesis'),('organized','organised'),('generalize','generalise'),('parameterization','parameterisation')]:s=re.sub(r'\b'+a+r'\b',b,s)
 if s!=p.text:p.text=s
# Put each block after the paragraph that motivates it. All first mentions remain in numerical order.
def insert_after(anchor,nodes):
 for node in nodes:anchor.addnext(node);anchor=node
for n,i in {1:16,2:52,3:59,4:63,5:75,6:108}.items():insert_after(anchors[i]._p,tables[n])
for n,i in {1:67,2:75,3:82,4:85,5:87,6:91}.items():
 anchor=tables[5][-1] if n==2 else anchors[i]._p
 insert_after(anchor,figures[n])
# Correct the literature table version and a vague schema label.
for t in DOC.tables:
 for row in t.rows:
  for cell in row.cells:
   s=cell.text.replace('Microglia preprint','Microglia clock').replace('Microglia evidence is a preprint.','Microglia evidence is from the 2025 peer-reviewed report.').replace('Feature contract','Feature definition')
   if s!=cell.text:cell.text=s
for p in DOC.paragraphs:
 if 'Microglia evidence is a preprint.' in p.text:p.text=p.text.replace('Microglia evidence is a preprint.','The microglial study is cited in its peer-reviewed 2025 version.')
# Three horizontal rules only: top, below the column header, and bottom.
def three_rules(table):
 pr=table._tbl.tblPr
 for x in list(pr.findall(qn('w:tblBorders'))):pr.remove(x)
 borders=OxmlElement('w:tblBorders')
 for name in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+name);e.set(qn('w:val'),'nil');borders.append(e)
 pr.append(borders)
 for ri,row in enumerate(table.rows):
  for cell in row.cells:
   cp=cell._tc.get_or_add_tcPr()
   for name in ['tcBorders','shd']:
    for e in list(cp.findall(qn('w:'+name))):cp.remove(e)
   bs=OxmlElement('w:tcBorders')
   for side in ['top','bottom','left','right']:
    e=OxmlElement('w:'+side);on=(ri==0 and side in ['top','bottom']) or (ri==len(table.rows)-1 and side=='bottom');e.set(qn('w:val'),'single' if on else 'nil')
    if on:e.set(qn('w:sz'),'8' if side=='top' or ri==len(table.rows)-1 else '4');e.set(qn('w:color'),'000000')
    bs.append(e)
   cp.append(bs);cell.vertical_alignment=1
   for p in cell.paragraphs:
    p.paragraph_format.line_spacing=1.08;p.paragraph_format.space_after=Pt(4)
    for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(9.5);run.font.bold=ri==0;run.font.color.rgb=RGBColor(0,0,0)
  if ri==0:
   prr=row._tr.get_or_add_trPr()
   if prr.find(qn('w:tblHeader')) is None:prr.append(OxmlElement('w:tblHeader'))
for t in DOC.tables:
 three_rules(t)
 for row in t.rows[:-1]:
  for cell in row.cells:
   for p in cell.paragraphs:p.paragraph_format.keep_with_next=True
for p in DOC.paragraphs:
 if p._p in [nodes[0] for nodes in tables.values()]+[nodes[1] for nodes in figures.values()]:
  p.style='Caption';p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(10);p.paragraph_format.line_spacing=1.1
  for run in p.runs:run.font.color.rgb=RGBColor(0,0,0)
 if not p.text.strip() and not p._p.xpath('.//w:drawing'):p._p.getparent().remove(p._p)
# Figure legends refer to completed controls rather than a deleted main-panel row.
for p in DOC.paragraphs:
 if p.text.startswith('A, paired error differences'):p.text=p.text.replace('the T-deletion control primarily removes explicit subset allocation.','the T-deletion control is reported separately in Supplementary Table S18.')
# Renumber references in document order, including inline tables and legends.
pattern=re.compile(r'\[(\d+(?:[ ,–-]+\d+)*)\]')
def expand(s):
 out=[]
 for part in s.split(','):
  bits=re.split('[–-]',part.strip());out.extend(range(int(bits[0]),int(bits[-1])+1))
 return out
order=[];placements=[]
for p in DOC._element.body.iter(qn('w:p')):
 text=''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()'))
 for m in pattern.finditer(text):
  for n in expand(m[1]):
   k=keymap[n]
   if k not in order:order.append(k)
   placements.append({'key':k,'original_number':n,'context':text,'review':'Citation attached to the supported description or methodological recommendation; literature performance not ranked across cohorts.'})
assert 30<len(order)<100 and len(order)==65,(len(order),set(keymap.values())-set(order))
nums={k:i+1 for i,k in enumerate(order)}
def recite(text):return pattern.sub(lambda m:'['+', '.join(str(i) for i in sorted({nums[keymap[n]] for n in expand(m[1])}))+']',text)
for p in DOC.paragraphs:
 if pattern.search(p.text):p.text=recite(p.text)
for t in DOC.tables:
 for row in t.rows:
  for cell in row.cells:
   for p in cell.paragraphs:
    if pattern.search(p.text):p.text=recite(p.text)
# Use indexed bibliographic metadata, preserving the publisher PDF volume-year for the mouse paper.
def clean(s):return html.unescape(re.sub('<[^>]+>','',html.unescape(s))).replace('\u2009',' ')
def bibliography(k):
 r=refs[k]['record'];ji=r.get('journalInfo') or {};j=ji.get('journal') or {};authors=[a.get('fullName') or a.get('collectiveName','') for a in r.get('authorList',{}).get('author',[])];authors=[a for a in authors if a];au=', '.join(authors[:3])+(', et al.' if len(authors)>3 else '.')
 year=2026 if k=='mouse' else ji.get('yearOfPublication') or r.get('pubYear');s=f"{au} {clean(r['title']).rstrip('.')}. {j.get('medlineAbbreviation') or j.get('title','')}. {year}"
 if ji.get('volume'):s+=';'+str(ji['volume'])
 if r.get('pageInfo'):s+=':'+r['pageInfo']
 return s+'. doi: '+r['doi']+'.'
DOC.add_heading('References',1)
for k in order:
 p=DOC.add_paragraph(str(nums[k])+'. '+bibliography(k));p.paragraph_format.line_spacing=1.1;p.paragraph_format.keep_together=True
 for run in p.runs:run.font.size=Pt(10)
for p in DOC.paragraphs:
 if p.style.name in ['Normal','List Bullet'] and not p.text.startswith(tuple(str(i)+'. ' for i in range(1,66))):p.paragraph_format.widow_control=True
 if p._p.xpath('.//w:drawing'):p.paragraph_format.keep_with_next=True
for style in ['Title','Heading 1','Heading 2','Caption']:
 st=DOC.styles[style];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
DOC.styles['Caption'].font.size=Pt(10);DOC.styles['Caption'].font.bold=True
# Replace the embedded images with the audited v4 assets when available.
for n,nodes in figures.items():
 image=nodes[0];rel=image.xpath('.//a:blip/@r:embed')
 if rel:
  name=next((R/'figures'/'main').glob(f'Figure_{n}_*.png'));DOC.part.related_parts[rel[0]]._blob=name.read_bytes()
DOC.styles['Normal'].paragraph_format.line_spacing=1.5
for p in DOC.paragraphs:
 if p.text=='Key points':p.paragraph_format.page_break_before=True
 if p.style.name=='List Bullet':p.paragraph_format.keep_together=True
 if p.style.name=='Caption':
  for run in p.runs:run.font.color.rgb=RGBColor(0,0,0)
for n,nodes in figures.items():
 from docx.text.paragraph import Paragraph
 Paragraph(nodes[2],DOC._body).paragraph_format.keep_together=True
 if n==6:
  extent=nodes[0].xpath('.//wp:extent')[0]
  oldcx=int(extent.get('cx'));oldcy=int(extent.get('cy'));newcx=int(Inches(5.4));newcy=int(oldcy*newcx/oldcx)
  extent.set('cx',str(newcx));extent.set('cy',str(newcy))
  for e in nodes[0].xpath('.//a:xfrm/a:ext'):e.set('cx',str(newcx));e.set('cy',str(newcy))

DOC.core_properties.title='Evaluating immune ageing clocks';DOC.core_properties.comments='';DOC.save(OUT/'Immune_ageing_BIB_review_v4.docx')
# Supplement retains its analytical content; update citations and three-rule formatting.
supp=Document(V/'deliverables/Immune_ageing_BIB_review_v3_Supplement.docx')
for p in supp.paragraphs:
 if pattern.search(p.text):p.text=recite(p.text)
 if 'preprint' in p.text.lower():p.text=p.text.replace('microglial featurisation','microglial featurisation').replace('Microglia: preprint.','Microglial featurisation: peer-reviewed study, 2025.').replace('preprint','peer-reviewed study')
 if p.text.startswith('The chronological map places'):
  p.text=p.text.replace('The microglial study is a peer-reviewed study.','The microglial study is cited in its peer-reviewed 2025 version.')
for t in supp.tables:
 three_rules(t)
 for row in t.rows:
  for cell in row.cells:
   for p in cell.paragraphs:
    if pattern.search(p.text):p.text=recite(p.text)
# Updated milestone artwork; the other supplementary images retain their verified source data.
for rel,part in supp.part.related_parts.items():
 if hasattr(part,'content_type') and part.content_type.startswith('image/'):
  # The first image is the milestone drawing.
  if not hasattr(supp,'_milestone_updated'):
   f=next((R/'figures'/'supplementary').glob('Figure_S1_*.png'));part._blob=f.read_bytes();supp._milestone_updated=True
supp.core_properties.title='Supplementary analyses for evaluating immune ageing clocks';supp.save(OUT/'Immune_ageing_BIB_review_v4_Supplement.docx')
with (R/'citation_placement_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=['number','key','doi','context','review']);w.writeheader()
 for a in placements:w.writerow({'number':nums[a['key']],'key':a['key'],'doi':refs[a['key']]['record']['doi'],'context':recite(a['context']),'review':a['review']})
with (R/'references_final.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['number','key','doi','reference','year'])
 for k in order:w.writerow([nums[k],k,refs[k]['record']['doi'],bibliography(k),2026 if k=='mouse' else refs[k]['record'].get('journalInfo',{}).get('yearOfPublication') or refs[k]['record'].get('pubYear')])
(R/'reference_numbers_v4.json').write_text(json.dumps(nums,indent=2),encoding='utf8')
(OUT/'manuscript_text_v4.txt').write_text('\n\n'.join(p.text for p in DOC.paragraphs),encoding='utf8')
print('Saved main and supplement; references',len(order))
