"""Descobre campanhas promocionais B2C de pneus ligeiros em Portugal via Google News RSS.
Filtro conservador: só envia para revisão resultados com sinais claros de pneus + promoção,
excluindo conteúdos editoriais, lançamentos de produto e segmentos fora do âmbito.
"""
import csv, os, re, hashlib, unicodedata
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

QUERIES = [
    '"pneus" promoção Portugal desconto',
    '"pneus" campanha Portugal reembolso',
    '"pneus" cashback Portugal',
    '"pneus" "oferta" Portugal automóvel',
    '"pneus" voucher Portugal automóvel',
    '"pneus" "na compra" Portugal',
    '"pneus" promoção Portugal Michelin',
    '"pneus" promoção Portugal Continental',
    '"pneus" promoção Portugal Bridgestone',
    '"pneus" promoção Portugal Goodyear',
    '"pneus" promoção Portugal Pirelli',
    '"pneus" promoção Portugal Hankook',
    '"pneus" promoção Portugal Norauto',
    '"pneus" promoção Portugal Feu Vert',
    '"pneus" promoção Portugal Confortauto',
    '"pneus" promoção Portugal Euromaster',
    '"pneus" promoção Portugal First Stop',
]
OUT='monitorizacao/candidatas.csv'
FIELDS=['candidate_id','detetada_em_utc','consulta','titulo','url','publicador','estado_validacao','notas','filter_score','filter_reasons']

PROMO=[
 r'promo[cç][aã]o',r'campanha',r'reembolso',r'cashback',r'desconto',
 r'voucher',r'vale(?:\s+de)?',r'cart[aã]o(?:\s+oferta)?',r'oferta',
 r'gr[aá]tis',r'brinde',r'na compra',r'compre',r'pague',r'ganhe',
 r'at[eé]\s+\d+[\s€%]',r'\d+\s?%\s+(?:de\s+)?desconto'
]
TYRE=[r'\bpneu(?:s)?\b',r'\btyre(?:s)?\b',r'\btire(?:s)?\b']
LIGHT=[
 r'autom[oó]vel',r'carro',r've[ií]culo(?:s)? ligeiro',r'pneus ligeiros',
 r'passageiro',r'turismo',r'suv',r'4x4',r'jante'
]
EXCLUDE=[
 r'\bmoto(?:s|ciclo|ciclos)?\b',r'motocicl',r'scooter',r'trail\b',
 r'cami[aã]o',r'pesados?',r'autocarro',r'agr[ií]cola',r'trator',
 r'bicicleta',r'ciclismo',r'compressor',r'press[aã]o dos pneus',
 r'lan[cç]a(?:mento|do|da| novos?)',r'apresenta novos?',r'novo pneu',
 r'teste(?:s)? de pneus',r'comparativo',r'review',r'ensaio',
 r'f[aá]brica',r'resultados financeiros',r'mercado de pneus',
 r'pneus chineses',r'tarifas?',r'importa[cç][aã]o'
]
COMMERCIAL_EXCLUDE=[r'pneu(?:s)? comercial',r've[ií]culos? comerciais?',r'frota(?:s)?']

def norm(s):
    return unicodedata.normalize('NFKC',s or '').lower()

def hit(patterns,text):
    return any(re.search(p,text,re.I) for p in patterns)

def score(title,publisher,query):
    t=norm(title); q=norm(query); reasons=[]; n=0
    if hit(TYRE,t): n+=3; reasons.append('pneus')
    if hit(PROMO,t): n+=4; reasons.append('sinal promocional')
    if hit(LIGHT,t): n+=2; reasons.append('ligeiros/automóvel')
    # Uma query promocional ajuda a descoberta, mas nunca substitui sinal promocional no título.
    if hit(PROMO,q): n+=1
    if hit(EXCLUDE,t):
        n-=10; reasons.append('exclusão temática')
    if hit(COMMERCIAL_EXCLUDE,t):
        n-=8; reasons.append('segmento comercial/frotas')
    # Gate obrigatório: o próprio título tem de falar de pneus e de uma mecânica/promessa promocional.
    eligible=hit(TYRE,t) and hit(PROMO,t) and not hit(EXCLUDE,t) and not hit(COMMERCIAL_EXCLUDE,t)
    return n,reasons,eligible

def main():
    os.makedirs('monitorizacao',exist_ok=True)
    # Reconstrói a fila a cada execução para que resultados antigos/irrelevantes não sobrevivam
    # a alterações dos filtros. O histórico validado vive no Supabase.
    rows={}
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    for query in QUERIES:
        url='https://news.google.com/rss/search?q='+quote(query)+'&hl=pt-PT&gl=PT&ceid=PT:pt-150'
        try:
            req=Request(url,headers={'User-Agent':'MarketScope/2.0 campaign-monitor'})
            with urlopen(req,timeout=25) as resp: xml=resp.read(3_000_000)
            root=ET.fromstring(xml)
            for item in root.findall('.//item'):
                title=(item.findtext('title') or '').strip()
                link=(item.findtext('link') or '').strip()
                pub=(item.findtext('source') or '').strip()
                if not link or not title: continue
                s,reasons,eligible=score(title,pub,query)
                if not eligible or s < 7: continue
                key=hashlib.sha1(link.encode()).hexdigest()[:12]
                if link not in rows:
                    rows[link]={'candidate_id':'CAND-'+key,'detetada_em_utc':now,'consulta':query,'titulo':title,'url':link,'publicador':pub,'estado_validacao':'Pendente de validação','notas':'Pré-filtrada automaticamente; confirmar elegibilidade, datas, mecânica e fonte primária.','filter_score':str(s),'filter_reasons':'; '.join(reasons)}
        except Exception as e:
            print(f'Falha na consulta {query!r}: {e}')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(sorted(rows.values(),key=lambda r:(int(r.get('filter_score') or 0),r['detetada_em_utc']),reverse=True))
    print(f'{len(rows)} candidatas elegíveis guardadas em {OUT}; validar manualmente.')

if __name__=='__main__': main()
