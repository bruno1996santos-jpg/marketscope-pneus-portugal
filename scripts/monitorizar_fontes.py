import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

CSV_PATH = "campanhas.csv"
STATE_PATH = "monitorizacao/fontes.json"
REPORT_PATH = "monitorizacao/relatorio.md"


def read_campaign_sources():
    urls = set()
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = (row.get("URL fonte / regulamento") or "").strip()
            if url.startswith("https://") or url.startswith("http://"):
                urls.add(url)
    return sorted(urls)


def fetch(url):
    try:
        req = Request(url, headers={"User-Agent": "MarketScope-Source-Monitor/1.0"})
        with urlopen(req, timeout=25) as response:
            body = response.read(2_000_000)
            return {"status": response.status, "sha256": hashlib.sha256(body).hexdigest(), "error": ""}
    except HTTPError as e:
        return {"status": e.code, "sha256": "", "error": str(e)}
    except (URLError, TimeoutError, Exception) as e:
        return {"status": None, "sha256": "", "error": str(e)}


def main():
    os.makedirs("monitorizacao", exist_ok=True)
    old = {}
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            old = json.load(f)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current = {}
    changes = []
    for url in read_campaign_sources():
        result = fetch(url)
        result["checked_at"] = now
        current[url] = result
        previous = old.get(url)
        if previous is None:
            changes.append(("Nova fonte", url, result))
        elif result["status"] != previous.get("status") or result["sha256"] != previous.get("sha256"):
            changes.append(("Fonte alterada", url, result))
        elif result["error"]:
            changes.append(("Erro de acesso", url, result))

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2, sort_keys=True)

    lines = ["# Monitorização automática de fontes — MarketScope", "", f"Verificação UTC: {now}", "",
             "> Esta verificação deteta alterações técnicas no conteúdo das páginas. Não confirma automaticamente novas campanhas nem altera os dados do dashboard; as alterações identificadas exigem validação humana.", ""]
    if changes:
        lines += [f"## Alterações/alertas ({len(changes)})", ""]
        for label, url, result in changes:
            lines.append(f"- **{label}** — [{url}]({url}) — HTTP: {result['status']}; {result['error'] or 'conteúdo/hash diferente da verificação anterior'}")
    else:
        lines += ["Sem alterações técnicas detetadas nas fontes acessíveis."]
    lines += ["", "## Estado das fontes", ""]
    for url, result in current.items():
        lines.append(f"- [{url}]({url}) — HTTP: {result['status']}; {'erro: ' + result['error'] if result['error'] else 'acesso concluído'}")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Verificadas {len(current)} fontes; {len(changes)} alertas.")


if __name__ == "__main__":
    main()
