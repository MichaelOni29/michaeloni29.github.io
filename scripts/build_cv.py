#!/usr/bin/env python3
"""
Rebuild cv.pdf from publications.json, so the downloadable CV always carries the
same citation figures and publication list as the website.

Runs every Monday in GitHub Actions, right after update_publications.py.
Edit the fixed CV sections (appointments, education, awards, ...) in BODY below.
"""
import datetime
import html
import json
import os
import re

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "publications.json"), encoding="utf-8"))
pubs, m = d["publications"], d.get("metrics", {})
e = html.escape


def fmt_authors(a):
    """'BK Jha, MO Oni' (Scholar style) -> 'B. K. Jha, M. O. Oni'; already-dotted names are kept."""
    out = []
    for n in (a or "").split(","):
        n = n.strip()
        mm = re.match(r"^([A-Z]{1,4}) (.+)$", n)
        out.append(" ".join(c + "." for c in mm.group(1)) + " " + mm.group(2) if mm else n)
    return ", ".join(x for x in out if x)


def bold_me(a):
    # Scholar writes the name several ways: M. O. Oni, M. Oni, MO ONI, O. O. Michael, O. Michael
    pat = r"(M\. (?:O\. )?Oni|Michael O\. Oni|Michael Oni|(?:O\. )?O\. Michael)"
    return re.sub(pat, r"<b>\1</b>", e(fmt_authors(a)), count=1, flags=re.I)


def tl(rows):
    return "<table class='tl'>" + "".join(
        f"<tr><td class='w'>{w}</td><td>{x}</td></tr>" for w, x in rows) + "</table>"


def year_key(p):
    return -(p.get("year") or 0), (p.get("title") or "").lower()


pubs = sorted(pubs, key=year_key)
items = []
for i, p in enumerate(pubs):
    doi = f" <a href='https://doi.org/{e(p['doi'])}'>doi:{e(p['doi'])}</a>" if p.get("doi") else ""
    yr = f" ({p['year']})" if p.get("year") else ""
    venue = f" <i>{e(p['venue'])}</i>." if p.get("venue") else ""
    items.append(f"<li><span class='n'>{len(pubs) - i}.</span><div>{bold_me(p.get('authors'))}{yr}. "
                 f"{e(p.get('title') or '')}.{venue}{doi}</div></li>")

try:
    asof = datetime.datetime.fromisoformat(d.get("updated", "").replace("Z", "+00:00")).strftime("%d %B %Y").lstrip("0")
except ValueError:
    asof = datetime.date.today().strftime("%B %Y")
source = "Google Scholar" if "Scholar" in (m.get("label", "") + d.get("source", "")) else "Citation figures"

BODY = f"""
<header>
  <div>
    <h1>Dr. Michael O. Oni</h1>
    <div class="role">Applied Mathematician · Heat Transfer &amp; Scientific Machine Learning</div>
    <div class="aff">Postdoctoral Fellow, Unit for Data Science and Computing, North-West University, South Africa<br>
    Senior Lecturer, Department of Mathematics, Ahmadu Bello University, Zaria, Nigeria</div>
  </div>
  <div class="contact">
    mooni@abu.edu.ng<br>michaeloni29@gmail.com<br>
    <a href="https://orcid.org/0000-0002-0272-4825">ORCID 0000-0002-0272-4825</a><br>
    <a href="https://scholar.google.com/citations?user=7PQsNQ4AAAAJ">Google Scholar</a> ·
    <a href="https://www.scopus.com/authid/detail.uri?authorId=57191926774">Scopus</a><br>
    <a href="https://www.webofscience.com/wos/author/record/X-7347-2019">Web of Science X-7347-2019</a><br>
    <a href="https://www.researchgate.net/profile/Michael-Oni">ResearchGate</a><br>
    <a href="https://michaeloni29.github.io">michaeloni29.github.io</a>
  </div>
</header>

<div class="metrics">
  <div><b>{m.get('citations', '—')}</b><span>citations</span></div>
  <div><b>{m.get('h_index', '—')}</b><span>h-index</span></div>
  <div><b>{m.get('i10_index', '—')}</b><span>i10-index</span></div>
  <div><b>{len(pubs)}</b><span>publications</span></div>
  <p>{source}, {asof}. Web of Science: 454 citations, h-index 14.</p>
</div>

<h2>Research interests</h2>
<p>Computational mathematics, fluid dynamics and heat transfer; natural and mixed convection in channels and annuli;
electroosmotic and electromagnetohydrodynamic microflows; entropy generation; non-Fourier (dual- and three-phase-lag)
heat conduction; spectral and semi-analytical methods; physics-informed neural networks and scientific machine learning.</p>

<h2>Appointments</h2>
{tl([("2026 – present", "<b>Postdoctoral Fellow</b>, Unit for Data Science and Computing, North-West University, South Africa"),
     ("2025 – present", "<b>Senior Lecturer</b>, Department of Mathematics, Ahmadu Bello University, Zaria"),
     ("2022 – 2025", "<b>Lecturer I</b>, Ahmadu Bello University, Zaria"),
     ("2019 – 2022", "<b>Lecturer II</b>, Ahmadu Bello University, Zaria"),
     ("2016 – 2019", "<b>Assistant Lecturer</b>, Ahmadu Bello University, Zaria"),
     ("2014 – 2016", "<b>Graduate Assistant</b>, Ahmadu Bello University, Zaria")])}

<h2>Education</h2>
{tl([("2021", "<b>PhD Mathematics</b>, Ahmadu Bello University, Zaria.<br><i>Thesis: A Study on Electroosmotic Natural and Mixed Convection Flows in Vertical Microgeometries with Isothermal and Isoflux Boundary Conditions</i>"),
     ("2016", "<b>MSc Mathematics</b>, Ahmadu Bello University, Zaria.<br><i>Dissertation: A Study on Natural Convection Flow in Cylindrical Geometries with Time-Periodic Heat Input</i>"),
     ("2012", "<b>BSc (Hons) Mathematics, First Class</b>, Ahmadu Bello University, Zaria")])}

<h2>Grants, awards &amp; innovation</h2>
{tl([("2025", "Principal Investigator, TETFund Institution-Based Research (IBR) Grant, Ahmadu Bello University"),
     ("2015", "Innovation: the <i>paraletrix</i>, a generalization of the rhotrix (<i>Afrika Matematika</i> 26, 871–885)"),
     ("2012", "Vice-Chancellor's Award of Excellence, ABU 2011/2012 Convocation"),
     ("2012", "Bronze medal, National Mathematics Competition for University Students (NAMCUS), National Mathematical Centre, Abuja")])}

<h2>Research supervision</h2>
{tl([("PhD", "Usman Rilwan · Electroosmotic natural convection of nanofluids with induced magnetic field · <i>Major supervisor, ongoing</i>"),
     ("PhD", "Luqman Azeez · Natural convection of nanofluids in a vertical channel with suction/injection · <i>Co-supervisor, ongoing</i>"),
     ("PhD", "Ismaila Oyelade · Dual-phase-lag natural convection in a vertical channel · <i>Co-supervisor, ongoing</i>"),
     ("MSc", "Fatai Mohammed · Entropy generation with isothermal/isoflux conditions · <i>Major supervisor, ongoing</i>"),
     ("MSc", "Henry Ibrahim · Temperature-dependent viscosity in natural and mixed convection · <i>Major supervisor, ongoing</i>"),
     ("MSc", "Shakira Adebayo · Heat and mass transfer in unsteady EMHD natural convection · <i>Major supervisor, 2026</i>"),
     ("MSc", "Ahmed Abdulmalik · Hall current effects on free convection in a porous channel · <i>Major supervisor, 2026</i>"),
     ("MSc", "Vampah Tizhe Peter · Entropy generation in MHD porous-channel flow with Navier slip · <i>Co-supervisor, 2026</i>"),
     ("MSc", "Usman Rilwan · Time-dependent natural convection with heat source/sink · <i>Major supervisor, 2021</i>")])}

<h2>Peer review</h2>
<p>92 verified reviews of 65 manuscripts (Web of Science), including <i>Heat Transfer – Asian Research</i>, <i>ZAMM</i>,
<i>Propulsion and Power Research</i>, <i>International Journal of Ambient Energy</i>, <i>Numerical Heat Transfer A &amp; B</i>,
<i>Journal of Thermophysics and Heat Transfer</i>, <i>International Journal of Numerical Methods for Heat &amp; Fluid Flow</i>,
<i>IEEE Transactions on Industrial Informatics</i>, <i>Physica Scripta</i> and <i>Engineering Applications of Computational Fluid Mechanics</i>.</p>

<h2>Teaching</h2>
<p>Undergraduate: Numerical Analysis I &amp; II, Engineering Calculus I &amp; II, Methods of Linear Algebra, Mathematical Methods,
Vectors, Algebra, Trigonometry, Sets and Number Systems, Discrete Structures. Postgraduate: Research Methodology and ICT (MATH 812);
Engineering Mathematics and Numerical Methods for the PGD Civil Engineering programme. Online tutor, ABU Distance Learning Centre (2020 – present).</p>

<h2>Conference presentations</h2>
{tl([("2024", "Two papers on EMHD and electrokinetic convection. 10th International Aegean Conferences on Innovation Technologies &amp; Engineering, İzmir, Türkiye"),
     ("2024", "Mixed convective rarefied gas flow with flow reversal and cubic density–temperature variation. 8th International Conference on Global Practice of Multidisciplinary Scientific Studies, Dubai, UAE"),
     ("2022", "Radially varying heat source/sink on MHD free convection in a concentric annulus. Ankara International Congress on Scientific Research VI, Türkiye (oral)"),
     ("2021", "Two oral presentations. 39th Annual Conference, Nigerian Mathematical Society, Redeemer's University, Ede"),
     ("2016", "Two papers. 35th Annual Conference, Nigerian Mathematical Society, FUT Minna"),
     ("2015", "52nd Annual National Conference, Mathematical Association of Nigeria, UNEC, Enugu")])}

<h2>Memberships &amp; service</h2>
{tl([("2025 –", "Nigerian Young Academy"), ("2014 –", "Mathematical Association of Nigeria"), ("2015 – 2021", "Nigerian Mathematical Society"),
     ("2026", "Developed an app for the Nigerian Young Academy celebrating members promoted to Professor")])}

<h2>Publications <span class="cnt">({len(pubs)})</span></h2>
<ol class="pubs">{''.join(items)}</ol>
<p class="foot">Publication list and citation figures as of {asof}. Referees available on request.</p>
"""

CSS = """
@page{size:A4}
*{box-sizing:border-box}
body{font-family:'Public Sans',Helvetica,Arial,sans-serif;font-size:9.4pt;line-height:1.45;color:#14232b;margin:0}
a{color:#0d5c73;text-decoration:none}
h1,h2{font-family:'Source Serif 4',Georgia,serif;margin:0}
header{display:flex;justify-content:space-between;gap:12mm;border-bottom:1.5pt solid #0d5c73;padding-bottom:4mm}
h1{font-size:23pt;font-weight:700;letter-spacing:-.01em}
.role{font-size:10.5pt;margin-top:1mm}
.aff{color:#5a6a72;margin-top:1.5mm;font-size:9pt}
.contact{text-align:right;font-size:8.6pt;line-height:1.55;white-space:nowrap}
.metrics{display:flex;flex-wrap:wrap;gap:0 9mm;align-items:baseline;margin:4mm 0 1mm}
.metrics div b{font-family:'Source Serif 4',Georgia,serif;font-size:14pt;color:#c4612a;margin-right:1.2mm}
.metrics div span{color:#5a6a72}
.metrics p{flex-basis:100%;margin:.5mm 0 0;font-size:8pt;color:#5a6a72}
h2{font-size:12pt;font-weight:600;color:#0d5c73;margin:5.5mm 0 2mm;padding-bottom:1mm;border-bottom:.5pt solid #d9e1e5;break-after:avoid}
h2 .cnt{font-weight:400;color:#5a6a72;font-size:10pt}
p{margin:0}
.tl{border-collapse:collapse;width:100%}
.tl td{vertical-align:top;padding:.8mm 0}
.tl td.w{width:27mm;color:#5a6a72;font-variant-numeric:tabular-nums;white-space:nowrap;padding-right:3mm}
.tl tr{break-inside:avoid}
.pubs{list-style:none;margin:0;padding:0}
.pubs li{display:flex;gap:2.5mm;padding:1mm 0;break-inside:avoid}
.pubs .n{width:7mm;flex:none;text-align:right;color:#5a6a72;font-variant-numeric:tabular-nums}
.pubs a{font-size:8.2pt}
.foot{margin-top:5mm;font-size:8pt;color:#5a6a72}
"""

FONTS = ("<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;"
         "0,8..60,600;0,8..60,700;1,8..60,400&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap'>")
doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>CV – Dr. Michael O. Oni</title>{FONTS}"
       f"<style>{CSS}</style></head><body>{BODY}</body></html>")

FOOTER = ("<div style='font-size:7pt;color:#5a6a72;width:100%;padding:0 16mm;display:flex;justify-content:space-between;"
          "font-family:Helvetica'><span>Michael O. Oni · Curriculum vitae</span>"
          "<span><span class='pageNumber'></span> / <span class='totalPages'></span></span></div>")

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.set_content(doc, wait_until="load")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
        page.evaluate("document.fonts.ready")
    except Exception:
        pass  # without the web fonts the CV falls back to Georgia/Helvetica
    page.pdf(path=os.path.join(ROOT, "cv.pdf"), format="A4", print_background=True,
             display_header_footer=True, header_template="<span></span>", footer_template=FOOTER,
             margin={"top": "16mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
    browser.close()

print(f"cv.pdf rebuilt: {m.get('citations')} citations, {len(pubs)} publications, as of {asof}")
