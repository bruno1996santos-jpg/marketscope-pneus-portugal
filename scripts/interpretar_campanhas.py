"""Interpretação heurística de candidatas: extrai sinais, nunca confirma factos automaticamente."""
import csv, os, re, json
from datetime import datetime, timezone
import unicodedata
SRC='monitorizacao/candidatas.csv'; OUT='monitorizacao/candidatas_estruturadas.json'
BRANDS=['Continental','Mabor','Uniroyal','Michelin','Pirelli','Goodyear','Hankook','Bridgestone','Dunlop','Cooper','Firestone','Nokian']
RETAILERS=['Norauto','Feu Vert','Confortauto','Euromaster','First Stop','Roady','Midas','Pneus Online']

def classify(text):
 t=text.lower(); found=[]
 rules=[('Reembolso',r'reembolso|cashback|devolu[cç][aã]o'),('Desconto direto',r'desconto|€\s?\d+\s?de desconto'),('Cartão oferta / voucher',r'voucher|cart[aã]o oferta|vale de'),('Oferta de brinde',r'oferta|gr[aá]tis|brinde'),('Garantia',r'garantia'),('Financiamento',r'financiamento|presta[cç][oõ]es')]
 for label,pat in rules:
  if re.search(pat,t): found.append(label)
 return found or ['Por determinar']
def money(text):
 vals=re.findall(r'(?:€\s?\d+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?\s?€)',text,re.I)
 return list(dict.fromkeys(vals))
MONTHS={'janeiro':1,'fevereiro':2,'março':3,'marco':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
def iso_pt_date(s, fallback_year=2026):
 s=s.strip().lower()
 m=re.search(r'(\d{1,2})\s+de\s+([a-záàâãéêíóôõúç]+)(?:\s+de\s+(\d{4}))?',s,re.I)
 if not m:return ''
 name=''.join(ch for ch in unicodedata.normalize('NFD',m.group(2)) if unicodedata.category(ch)!='Mn')
 month=MONTHS.get(name)
 if not month:return ''
 year=int(m.group(3) or fallback_year)
 try:return f'{year:04d}-{month:02d}-{int(m.group(1)):02d}'
 except:return ''
def inferred_period(dates, official):
 if not official or len(dates)<2:return ('','')
 a,b=iso_pt_date(dates[0]),iso_pt_date(dates[1])
 if a and b and a<=b:return (a,b)
 return ('','')
def main():
 os.makedirs('monitorizacao',exist_ok=True); out=[]
 if not os.path.exists(SRC):
  print('Sem candidatas por interpretar.'); return
 with open(SRC,encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   text=' '.join([r.get('titulo',''),r.get('publicador',''),r.get('notas',''),r.get('filter_reasons','')]); low=text.lower()
   brands=[x for x in BRANDS if x.lower() in low]; retailers=[x for x in RETAILERS if x.lower() in low]
   dates=re.findall(r'\b(\d{1,2}\s+de\s+[A-Za-zÀ-ÿçÇ]+(?:\s+de\s+\d{4})?)\b',text,re.I)
   dates=list(dict.fromkeys(dates))
   mech=classify(text)
   if re.search(r'compra\s+e\s+montagem\s+de\s+2\s+ou\s+4\s+pneus',text,re.I): mech=['Compra e montagem de 2 ou 4 pneus']
   elif re.search(r'(?:compra\s+e\s+)?montagem\s+de[^.!?]{0,30}2\s+pneus',text,re.I): mech=['Compra/montagem de pelo menos 2 pneus']
   official='fonte oficial' in low
   start,end=inferred_period(dates,official)
   vals=money(text)
   benefits=classify(text)
   offer=('Valores detetados na fonte: '+', '.join(vals)) if vals else ''
   conditions=r.get('notas','')
   out.append({**r,'marca_sugerida':brands[0] if len(brands)==1 else (' / '.join(brands) if brands else ''),'retalhista_sugerido':retailers[0] if len(retailers)==1 else ' / '.join(retailers),'mecanicas_sugeridas':mech,'beneficio_sugerido':' / '.join(benefits),'oferta_sugerida':offer,'condicoes_sugeridas':conditions,'valores_detetados':vals,'datas_detetadas':dates,'data_inicio':start,'data_fim':end,'ambito':'Portugal' if ('sinal portugal' in low or 'portugal' in low) else 'Portugal? Confirmar','publico_alvo':'Pneus ligeiros? Confirmar','resumo_interpretacao':('Extração automática da fonte oficial/notas; datas e valores pré-preenchidos quando existe evidência estruturada; confirmar antes de aprovar.' if official else 'Extração automática do resultado de pesquisa; consultar a fonte original.'),'estado_validacao':r.get('estado_validacao','Pendente de validação'),'validado_por':'','observacoes_revisor':''})
 with open(OUT,'w',encoding='utf-8') as f: json.dump({'gerado_em':datetime.now(timezone.utc).isoformat(),'aviso':'Sugestões automáticas, não verificadas. Validar com a fonte primária.','campanhas':out},f,ensure_ascii=False,indent=2)
 print(f'{len(out)} registos estruturados em {OUT}')
if __name__=='__main__': main()
