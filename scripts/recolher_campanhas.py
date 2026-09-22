"""Descobre potenciais campanhas via Google News RSS e coloca-as em revisão humana.
Não publica campanhas diretamente no dashboard: os resultados são pistas, não factos verificados.
"""
import csv, os, re, hashlib
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

QUERIES = [
    'pneus promoção Portugal Michelin', 'pneus campanha Portugal Pirelli',
    'pneus promoção Portugal Goodyear', 'pneus campanha Portugal Hankook',
    'pneus promoção Portugal Continental', 'pneus campanha Portugal Bridgestone',
    'pneus promoção Portugal Norauto', 'pneus campanha Portugal Feu Vert',
    'pneus campanha Portugal Confortauto', 'oferta pneus Portugal reembolso',
    'promoção pneus ligeiros Portugal 2026'
]
OUT = 'monitorizacao/candidatas.csv'
FIELDS = ['candidate_id','detetada_em_utc','consulta','titulo','url','publicador','estado_validacao','notas']

def main():
    os.makedirs('monitorizacao', exist_ok=True)
    rows = {}
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f): rows[r.get('url','')] = r
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for query in QUERIES:
        url = 'https://news.google.com/rss/search?q=' + quote(query) + '&hl=pt-PT&gl=PT&ceid=PT:pt-150'
        try:
            req = Request(url, headers={'User-Agent':'MarketScope/1.0 campaign-monitor'})
            with urlopen(req, timeout=25) as resp: xml = resp.read(3_000_000)
            root = ET.fromstring(xml)
            for item in root.findall('.//item'):
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                pub = (item.findtext('source') or '').strip()
                if not link or not title: continue
                key = hashlib.sha1(link.encode()).hexdigest()[:12]
                if link not in rows:
                    rows[link] = {'candidate_id':'CAND-'+key,'detetada_em_utc':now,'consulta':query,'titulo':title,'url':link,'publicador':pub,'estado_validacao':'Pendente de validação','notas':'Resultado de pesquisa RSS; confirmar na fonte primária antes de integrar.'}
        except Exception as e:
            print(f'Falha na consulta {query!r}: {e}')
    with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(sorted(rows.values(), key=lambda r:r['detetada_em_utc'], reverse=True))
    print(f'{len(rows)} candidatas guardadas em {OUT}; validar manualmente.')

if __name__ == '__main__': main()
