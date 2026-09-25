"""Interpretação heurística de candidatas: extrai sinais, nunca confirma factos automaticamente."""
import csv, os, re, json
from datetime import datetime, timezone
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
   out.append({**r,'marca_sugerida':brands[0] if len(brands)==1 else (' / '.join(brands) if brands else ''),'retalhista_sugerido':retailers[0] if len(retailers)==1 else ' / '.join(retailers),'mecanicas_sugeridas':mech,'valores_detetados':money(text),'datas_detetadas':dates,'data_inicio':'','data_fim':'','ambito':'Portugal' if ('sinal portugal' in low or 'portugal' in low) else 'Portugal? Confirmar','publico_alvo':'Pneus ligeiros? Confirmar','resumo_interpretacao':('Extração automática da fonte oficial/notas; datas detetadas não são assumidas como início/fim sem validação.' if official else 'Extração automática do resultado de pesquisa; consultar a fonte original.'),'estado_validacao':r.get('estado_validacao','Pendente de validação'),'validado_por':'','observacoes_revisor':''})
 with open(OUT,'w',encoding='utf-8') as f: json.dump({'gerado_em':datetime.now(timezone.utc).isoformat(),'aviso':'Sugestões automáticas, não verificadas. Validar com a fonte primária.','campanhas':out},f,ensure_ascii=False,indent=2)
 print(f'{len(out)} registos estruturados em {OUT}')
if __name__=='__main__': main()
