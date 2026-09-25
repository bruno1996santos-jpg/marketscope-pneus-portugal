"""Descobre campanhas promocionais B2C de pneus ligeiros em Portugal via Google News RSS.
Filtro conservador: só envia para revisão resultados com sinais claros de pneus + promoção,
excluindo conteúdos editoriais, lançamentos de produto e segmentos fora do âmbito.
"""
import csv, os, re, hashlib, unicodedata
from datetime import datetime, timezone
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# As fontes abaixo espelham a monitorização diária do MarketScope:
# marcas oficiais + redes/retalhistas + pesquisa complementar.
SOURCES = {
    'Continental': ['continental-tires.com'],
    'Michelin': ['michelin.pt'],
    'Pirelli': ['pirelli.com'],
    'Goodyear': ['goodyear.eu'],
    'Hankook': ['hankooktire.com'],
    'Bridgestone': ['bridgestone.pt', 'bridgestone-emia.com', 'promocoes.bridgestone.pt'],
    'Norauto': ['norauto.pt'],
    'Feu Vert': ['feuvert.pt'],
    'Confortauto': ['confortauto.pt'],
    'Euromaster': ['euromaster.pt'],
}

# Páginas oficiais promocionais conhecidas e verificadas. São consultadas diretamente
# em cada execução; Google News fica como canal complementar de descoberta.
OFFICIAL_PAGES = [
    ('Continental','https://www.continental-tires.com/pt/pt/pneus-promocao/'),
    ('Michelin Concessionários','https://www.michelin.pt/promocoes-michelin/concessionarios-2026'),
    ('Michelin Euromaster','https://www.michelin.pt/promocoes-michelin/euromaster-2026'),
    ('Pirelli','https://www.pirelli.com/tyres/pt-pt/carro/ofertas-promocoes'),
    ('Goodyear','https://www.goodyear.eu/pt_pt/consumer/promotion-hub/disfrute-ao-maximo-may-2026-portugal--pid-7004/terms-and-conditions.html'),
    ('Cooper','https://www.goodyear.eu/pt_pt/consumer/promotion-hub/national-promotion-sell-out-may-portugal-cooper-pid-6903/terms-and-conditions.html'),
    ('Norauto','https://www.norauto.pt/e/marca-pneu-norauto.html'),
    ('Goodyear / Norauto','https://www.norauto.pt/e/marca-pneu-goodyear.html'),
    ('Norauto Pneus','https://www.norauto.pt/e/pneu.html'),
    ('Hankook / Confortauto','https://premioshk.pt/bases-legales'),
    ('Bridgestone','https://promocoes.bridgestone.pt/'),
    ('Continental / Euromaster','https://www.euromaster.pt/promocao/pneus-continental'),
]

QUERIES = [
    '"pneus" promoção Portugal desconto',
    '"pneus" campanha Portugal reembolso',
    '"pneus" cashback Portugal',
    '"pneus" "oferta" Portugal automóvel',
    '"pneus" voucher Portugal automóvel',
    '"pneus" "na compra" Portugal',
]
for source in SOURCES:
    QUERIES += [
        f'"pneus" promoção Portugal "{source}"',
        f'"pneus" campanha Portugal "{source}"',
        f'"pneus" desconto Portugal "{source}"',
        f'"pneus" reembolso Portugal "{source}"',
        f'"pneus" oferta Portugal "{source}"',
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
 r'pneus chineses',r'tarifas?',r'importa[cç][aã]o',
 r'c[aâ]maras? de ar',r'\bburaco(?:s)?\b',r'indemniza[cç][aã](?:o|ões)',
 r'campanha de sensibiliza[cç][aã]o',r'sensibiliza[cç][aã]o',
 r'estrela(?:s)? michelin',r'chef(?:s)?',r'restaurante(?:s)?'
]
COMMERCIAL_EXCLUDE=[r'pneu(?:s)? comercial',r've[ií]culos? comerciais?',r'frota(?:s)?']
BIKE_PUBLISHERS=[r'mountainbikes?',r'ciclismo',r'bike']
PORTUGAL_SIGNAL=[r'\bportugal\b',r'\bportugu[eê]s(?:a|es|as)?\b',r'\bnacional\b']
PT_RETAILERS=[r'norauto',r'feu vert',r'confortauto',r'euromaster',r'first stop',r'roady',r'midas']

def norm(s):
    return unicodedata.normalize('NFKC',s or '').lower()

def hit(patterns,text):
    return any(re.search(p,text,re.I) for p in patterns)

def score(title,publisher,query):
    t=norm(title); p=norm(publisher); q=norm(query); reasons=[]; n=0
    if hit(TYRE,t): n+=3; reasons.append('pneus')
    if hit(PROMO,t): n+=4; reasons.append('sinal promocional')
    if hit(LIGHT,t): n+=2; reasons.append('ligeiros/automóvel')
    # Uma query promocional ajuda a descoberta, mas nunca substitui sinal promocional no título.
    if hit(PROMO,q): n+=1
    if hit(EXCLUDE,t):
        n-=10; reasons.append('exclusão temática')
    if hit(COMMERCIAL_EXCLUDE,t):
        n-=8; reasons.append('segmento comercial/frotas')
    if hit(BIKE_PUBLISHERS,p):
        n-=10; reasons.append('fonte de ciclismo')
    # Sinal geográfico: Portugal no título ou retalhista com operação nacional conhecida.
    geo=hit(PORTUGAL_SIGNAL,t) or hit(PT_RETAILERS,t)
    if geo: n+=3; reasons.append('sinal Portugal')
    # Gate obrigatório: pneus + promoção, sem exclusões. Resultados sem sinal geográfico
    # continuam possíveis para revisão, mas exigem evidência automóvel/ligeiros e score superior.
    eligible=hit(TYRE,t) and hit(PROMO,t) and not hit(EXCLUDE,t) and not hit(COMMERCIAL_EXCLUDE,t) and not hit(BIKE_PUBLISHERS,p)
    # MarketScope é exclusivamente Portugal: sem evidência geográfica no próprio resultado,
    # a notícia não entra na fila. Evita promoções estrangeiras como Campneus/Elo.
    if eligible and not geo: eligible=False
    return n,reasons,eligible

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self,data):
        if data and data.strip(): self.parts.append(data.strip())

TRUSTED_PT_HOSTS={'promocoes.bridgestone.pt','www.norauto.pt','norauto.pt','www.euromaster.pt','euromaster.pt','premioshk.pt'}
def official_candidate(brand,url,now):
    """Lê diretamente uma página oficial e cria candidata apenas com sinais fortes de campanha PT."""
    try:
        req=Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36','Accept-Language':'pt-PT,pt;q=0.9,en;q=0.7','Accept':'text/html,application/xhtml+xml'})
        with urlopen(req,timeout=25) as resp:
            raw=resp.read(2_000_000).decode('utf-8','ignore')
        parser=TextExtractor(); parser.feed(raw)
        text=' '.join(parser.parts)
        t=norm(text)
        # Página oficial tem de demonstrar Portugal + promoção + pneus e não pode declarar
        # explicitamente que não existem promoções em vigor.
        inactive=hit([r'n[aã]o existem promo[cç][oõ]es em vigor',r'de momento n[aã]o existem promo[cç][oõ]es em vigor',r'sem promo[cç][oõ]es em vigor'],t)
        host=urlparse(url).hostname or ''
        pt_source=hit(PORTUGAL_SIGNAL,t) or host in TRUSTED_PT_HOSTS
        eligible=hit(TYRE,t) and hit(PROMO,t) and pt_source and not inactive
        if not eligible: return None
        key=hashlib.sha1(url.encode()).hexdigest()[:12]
        # Extrai pistas úteis para a revisão sem inventar dados.
        dates=re.findall(r'\b(?:de\s+)?(\d{1,2}\s+de\s+[a-zç]+(?:\s+de\s+\d{4})?)\b',text,re.I)[:4]
        euros=re.findall(r'\b(?:até\s+)?\d+(?:[.,]\d{1,2})?\s?€\b',text,re.I)[:8]
        qty=re.findall(r'\b(?:compra|compre|montagem|monte)[^.!?]{0,80}\b[24]\s+pneus\b',text,re.I)[:4]
        evidence=[]
        if dates: evidence.append('datas: '+', '.join(dict.fromkeys(dates)))
        if euros: evidence.append('valores: '+', '.join(dict.fromkeys(euros)))
        if qty: evidence.append('mecânica: '+' | '.join(dict.fromkeys(qty)))\n        if benefits: evidence.append('benefício: '+' | '.join(dict.fromkeys(x.strip() for x in benefits)))
        summary='; '.join(evidence) if evidence else 'detalhes por confirmar'
        return {'candidate_id':'CAND-'+key,'detetada_em_utc':now,'consulta':'fonte oficial direta',
                'titulo':f'{brand} — promoção/campanha detetada em fonte oficial',
                'url':url,'publicador':brand,'estado_validacao':'Pendente de validação',
                'notas':'Detetada diretamente em fonte oficial. Extração automática: '+summary+'. Confirmar elegibilidade e vigência.',
                'filter_score':'15','filter_reasons':'fonte oficial; pneus; sinal promocional; sinal Portugal'}
    except Exception as e:
        print(f'Falha na fonte oficial {brand} {url}: {e}')
        return None

def main():
    os.makedirs('monitorizacao',exist_ok=True)
    # Reconstrói a fila a cada execução para que resultados antigos/irrelevantes não sobrevivam
    # a alterações dos filtros. O histórico validado vive no Supabase.
    rows={}
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    for brand,url in OFFICIAL_PAGES:
        r=official_candidate(brand,url,now)
        if r: rows[url]=r
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
