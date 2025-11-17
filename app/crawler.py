import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback
import re
OUTPUT_FILE = "/home/thorsten/_site/frontend/articles.html"

SOURCES = {
    # BRASIL
    "Folha - Mercado de Trabalho": "https://www1.folha.uol.com.br/folha-topicos/mercado-de-trabalho/",
    "Estadão - Carreiras": "https://economia.estadao.com.br/noticias/geral",
    "G1 - Economia": "https://g1.globo.com/economia/",
    "UOL Empregos": "https://economia.uol.com.br/empregos-e-carreiras/",
    "R7 Emprego": "https://noticias.r7.com/economia",
    "Terra Empregos": "https://www.terra.com.br/noticias/",
    "CNN Brasil Negócios": "https://www.cnnbrasil.com.br/business/",
    "Exame - Carreira": "https://exame.com/carreira/",
    "Veja - Trabalho": "https://veja.abril.com.br/noticias-sobre/trabalho/",
    "Forbes Brasil - Trabalho": "https://forbes.com.br/noticias-sobre/trabalho/",
    "IstoÉ Dinheiro": "https://istoedinheiro.com.br/carreira/",
    "Você S/A": "https://vocesa.abril.com.br/",
    "PEGN": "https://revistapegn.globo.com/",
    "CanalTech": "https://canaltech.com.br/",
    "TecMundo": "https://www.tecmundo.com.br/",
    "Olhar Digital": "https://olhardigital.com.br/",
    "InfoJobs Blog": "https://www.infojobs.com.br/blog/",
    "Catho Blog": "https://www.catho.com.br/carreiras/",
    "Vagas.com Insights": "https://www.vagas.com.br/profissoes/artigos",
    "LinkedIn Brasil Blog": "https://www.linkedin.com/pulse/"

    # INTERNACIONAIS
    ,"BBC Worklife": "https://www.bbc.com/worklife",
    "Reuters Employment": "https://www.reuters.com/business/",
    "The Guardian Work & Careers": "https://www.theguardian.com/work-in-progress",
    "FT Work & Careers": "https://www.ft.com/work-careers",
    "NYT Business Work": "https://www.nytimes.com/section/business",
    "TechCrunch Future of Work": "https://techcrunch.com/tag/future-of-work/",
    "WIRED Automation": "https://www.wired.com/tag/automation/",
    "The Verge AI": "https://www.theverge.com/artificial-intelligence",
    "MIT Tech Review": "https://www.technologyreview.com/",
    "Gig Economy Hub": "https://www.gigeconomydata.org/",
    "Fast Company – Future of Work": "https://www.fastcompany.com/section/future-of-work",
    "Quartz Future of Work": "https://qz.com/work",
    "Axios Future of Work": "https://www.axios.com/future-of-work",
    "SHRM": "https://www.shrm.org/",
    "Indeed Hiring Lab": "https://www.hiringlab.org/"

    # ORGANIZAÇÕES
    ,"WEF Future of Jobs": "https://www.weforum.org/reports/",
    "OECD Employment": "https://www.oecd.org/employment/",
    "McKinsey Employment": "https://www.mckinsey.com/featured-insights",
    "Bain Future of Work": "https://www.bain.com/insights/",
    "PwC Workforce": "https://www.pwc.com/gx/en/issues/upskilling.html",
    "Deloitte Insights Workforce": "https://www2.deloitte.com/insights/",
    "IBGE Emprego": "https://www.ibge.gov.br/estatisticas/sociais/trabalho.html",
    "OIT ILO": "https://www.ilo.org/global/lang--en/index.htm",
    "World Bank Jobs": "https://www.worldbank.org/en/topic/jobsanddevelopment",
    "IMF Labor Market": "https://www.imf.org/en/Topics"

    # GREEN JOBS
    ,"IEA Clean Energy": "https://www.iea.org/",
    "IRENA Renewable Jobs": "https://www.irena.org/",
    "ClimateTech VC": "https://climatetechvc.org/",
    "Bloomberg Green": "https://www.bloomberg.com/green",
    "Nature Sustainability": "https://www.nature.com/natsustain/"
}


def extract_links(url):
    """Return list of (title, link) from news pages."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")

        links = []
        for a in soup.find_all("a"):
            text = (a.get_text() or "").strip()
            href = a.get("href")

            if not href or len(text) < 5:
                continue
            if href.startswith("/"):
                href = url.rstrip("/") + href

            links.append((text, href))

        return links[:15]   # limit to avoid giant files

    except Exception as e:
        print(f"[ERROR] Failed crawling {url}: {e}")
        traceback.print_exc()
        return []


def generate_html(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>Artigos</title></head><body>")
        f.write(f"<h1>Artigos coletados – {datetime.now().strftime('%d/%m/%Y')}</h1>")

        for source, items in results.items():
            f.write(f"<h2>{source}</h2><ul>")
            for title, link in items:
                f.write(f"<li><a href='{link}' target='_blank'>{title}</a></li>")
            f.write("</ul>")

        f.write("</body></html>")


if __name__ == "__main__":
    print("Starting crawler...")

    all_results = {}
    for name, url in SOURCES.items():
        print(f"Crawling: {name}")
        all_results[name] = extract_links(url)

    print("Generating HTML...")
    generate_html(all_results)

    print(f"Finished! Output saved to {OUTPUT_FILE}")
headers = {"User-Agent": "Mozilla/5.0"}

# ----------------------------------------------------------
# Função util para extrair percentuais do texto
# ----------------------------------------------------------
def extract_percent(text):
    matches = re.findall(r"\d{1,3}(?:\.\d+)?%", text)
    return matches if matches else []


# ----------------------------------------------------------
# Fonte 1 — Fórum Econômico Mundial
# ----------------------------------------------------------
def crawl_wef():
    url = "https://www.weforum.org/agenda/archive/future-of-work/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    articles = soup.select("a.card__link")
    results = []

    for a in articles[:10]:
        link = "https://www.weforum.org" + a.get("href")
        title = a.get_text(strip=True)

        article_r = requests.get(link, headers=headers)
        art = BeautifulSoup(article_r.text, "html.parser")
        content = art.get_text(" ", strip=True)

        perc = extract_percent(content)

        results.append({
            "source": "WEF",
            "title": title,
            "url": link,
            "percentages": perc
        })

    return results


# ----------------------------------------------------------
# Fonte 2 — ILO (ONU: Organização Internacional do Trabalho)
# ----------------------------------------------------------
def crawl_ilo():
    url = "https://www.ilo.org/global/about-the-ilo/news/WCMS_coverage/lang--en/index.htm"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for link in soup.select("a.title")[:10]:
        href = "https://www.ilo.org" + link.get("href")
        title = link.get_text(strip=True)

        art_r = requests.get(href, headers=headers)
        art = BeautifulSoup(art_r.text, "html.parser")
        content = art.get_text(" ", strip=True)
        perc = extract_percent(content)

        results.append({
            "source": "ILO",
            "title": title,
            "url": href,
            "percentages": perc
        })

    return results


# ----------------------------------------------------------
# Fonte 3 — OECD
# ----------------------------------------------------------
def crawl_oecd():
    url = "https://www.oecd.org/employment/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for a in soup.select("a.oecdnews-link")[:10]:
        link = a.get("href")
        if not link.startswith("http"):
            link = "https://www.oecd.org" + link
        title = a.get_text(strip=True)

        art_r = requests.get(link, headers=headers)
        art = BeautifulSoup(art_r.text, "html.parser")
        content = art.get_text(" ", strip=True)
        perc = extract_percent(content)

        results.append({
            "source": "OECD",
            "title": title,
            "url": link,
            "percentages": perc
        })

    return results


# ----------------------------------------------------------
# Fonte 4 — Relatórios McKinsey
# ----------------------------------------------------------
def crawl_mckinsey():
    url = "https://www.mckinsey.com/featured-insights/future-of-work"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for a in soup.select("a.insights-card")[:10]:
        link = "https://www.mckinsey.com" + a.get("href")
        title = a.get_text(strip=True)

        art_r = requests.get(link, headers=headers)
        art = BeautifulSoup(art_r.text, "html.parser")
        content = art.get_text(" ", strip=True)
        perc = extract_percent(content)

        results.append({
            "source": "McKinsey",
            "title": title,
            "url": link,
            "percentages": perc
        })

    return results


# ----------------------------------------------------------
# Agregador final
# ----------------------------------------------------------
def crawl_trends():
    data = {
        "wef": crawl_wef(),
        "ilo": crawl_ilo(),
        "oecd": crawl_oecd(),
        "mckinsey": crawl_mckinsey(),
    }
    return data


# ----------------------------------------------------------
# Execução de teste
# ----------------------------------------------------------
if __name__ == "__main__":
    trends = crawl_trends()
    for source, items in trends.items():
        print(f"\n=== {source.upper()} ===")
        for item in items:
            print(item["title"])
            print("   ➤ % encontrados:", item["percentages"])
            print("   ➤ URL:", item["url"])
