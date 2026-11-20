"""Renderiza las tarjetas SVG del perfil de GitHub a partir del calendario público."""

import argparse
import base64
import json
import re
from calendar import monthrange
from collections import Counter
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
CALENDAR_URL = "https://github.com/users/gpazop/contributions"
OAT_MILK = "#f3ebdd"
PROFILE_EDGE = "#557064"
FOREST_GREEN = "#204638"
TOMATO_RED = "#bc352a"
CHART_RULE = "#c8cbb9"
HEAT = ("#e6dece", "#b4c4ad", "#819d83", "#54765d", FOREST_GREEN)
MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
STYLE = """
text { font-family: 'Segoe UI', system-ui, sans-serif; }
.name { font-family: Georgia, 'Times New Roman', serif; font-weight: 700; }
.mono { font-family: Consolas, 'Liberation Mono', monospace; letter-spacing: 1px; }
.rise { animation: rise .75s cubic-bezier(.2,.65,.3,1) both; }
.scan { animation: scan 1.3s .18s ease-out both; transform-origin: 50% 50%; }
.lit { animation: lit .4s ease-out both; }
.bar { transform-box: fill-box; transform-origin: bottom; animation: bar .65s ease-out both; }
@keyframes rise { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes scan { from { opacity: 0; transform: translateX(10px); } to { opacity: 1; transform: none; } }
@keyframes lit { from { opacity: .25; } to { opacity: 1; } }
@keyframes bar { from { transform: scaleY(.03); } to { transform: scaleY(1); } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
"""
HERO_STYLE = """
.handle-marker { animation: handle-pulse 1.6s ease-in-out infinite; }
@keyframes handle-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: .27; }
}
@media (prefers-reduced-motion: reduce) { .name-light { display: none; } }
"""
CHART_STYLE = """
.chart-title { font-family: 'Instrument Serif', Georgia, serif; font-weight: 400; }
.chart-italic { font-style: italic; }
.chart-label, .chart-label text { font-family: 'Geist Mono', Consolas, monospace; font-weight: 400; }
"""


class ContributionCalendar(HTMLParser):
    """Asocia cada celda del calendario de GitHub con su conteo visible."""

    def __init__(self):
        super().__init__()
        self.days = {}
        self.labels = {}
        self.tooltip = None
        self.heading = None
        self.total = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in attrs.get("class", "").split():
            self.days[attrs["id"]] = (date.fromisoformat(attrs["data-date"]), int(attrs["data-level"]))
        if tag == "tool-tip":
            self.tooltip = attrs.get("for")
            if self.tooltip in self.days:
                self.labels[self.tooltip] = ""
        if attrs.get("id") == "js-contribution-activity-description":
            self.heading = ""

    def handle_data(self, data):
        if self.tooltip in self.labels:
            self.labels[self.tooltip] += data
        if self.heading is not None:
            self.heading += data

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip = None
        if tag == "h2" and self.heading is not None:
            number = re.match(r"\s*([0-9,]+)\s+contributions?\b", self.heading)
            self.total = int(number[1].replace(",", "")) if number else None
            self.heading = None

    def records(self):
        result = []
        for key, (day, level) in self.days.items():
            label = self.labels.get(key, "").strip()
            count = re.match(r"([\d,]+) contributions?\b", label)
            if count:
                total = int(count[1].replace(",", ""))
            elif label.startswith("No contributions"):
                total = 0
            else:
                raise ValueError(f"Falta el conteo público para {day.isoformat()}")
            if not 0 <= level <= 4:
                raise ValueError(f"Nivel de actividad fuera de rango para {day.isoformat()}")
            result.append((day, level, total))

        result.sort()
        dates = [day for day, _, _ in result]
        if not 360 <= len(dates) <= 373 or any(
            later - earlier != timedelta(days=1) for earlier, later in zip(dates, dates[1:])
        ):
            raise ValueError("El calendario público está incompleto. Se conservan las tarjetas anteriores.")
        if sum(count for _, _, count in result) != self.total:
            raise ValueError("Los conteos del calendario y el total de GitHub no coinciden.")
        return result


def write_svg(name, width, height, description, body, *, extra_style=""):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" font-family="sans-serif">
<title>{escape(description)}</title>
<style>{STYLE}{extra_style}</style>
{body}
</svg>
'''
    (CARDS / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")


def hero_name(outlines, x, pazo_baseline, pazo_size, guillermo_baseline, guillermo_size):
    pazo = outlines["Pazo"]
    guillermo = outlines["Guillermo"]
    return f'''
<g aria-hidden="true">
  <defs>
    <linearGradient id="blue-light" gradientUnits="userSpaceOnUse" x1="-1.1" y1=".53" x2="-.12" y2=".26">
      <stop offset="0" stop-color="#60baff" stop-opacity="0"/>
      <stop offset=".31" stop-color="#72c3ff" stop-opacity=".7"/>
      <stop offset=".5" stop-color="#d2edff"/>
      <stop offset=".7" stop-color="#79caff" stop-opacity=".65"/>
      <stop offset="1" stop-color="#60baff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate"
                        values="0 0;5.4 0;5.4 0" keyTimes="0;.43;1"
                        begin="1.3s" dur="7s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <path d="{pazo}" transform="translate({x} {pazo_baseline}) scale({pazo_size} {-pazo_size})" fill="{FOREST_GREEN}"/>
  <g transform="translate({x} {guillermo_baseline}) scale({guillermo_size} {-guillermo_size})">
    <path d="{guillermo}" fill="{TOMATO_RED}"/>
    <path class="name-light" d="{guillermo}" fill="url(#blue-light)"/>
  </g>
</g>'''


def hero_handle(outline, x, baseline):
    return f'''
<g transform="translate({x} {baseline})" aria-label="@gpazop">
  <rect class="handle-marker" y="-10" width="8" height="8" rx="1.5" fill="#2f55ff"/>
  <path d="{outline}" transform="translate(17 0) scale(14 -14)" fill="{FOREST_GREEN}"/>
</g>'''


def hero():
    portrait = base64.b64encode((ROOT / "scripts" / "retrato.png").read_bytes()).decode("ascii")
    outlines = json.loads((ROOT / "scripts" / "nombre-instrument-serif.json").read_text(encoding="utf-8"))
    handle = (ROOT / "scripts" / "usuario-geist-mono.path").read_text(encoding="utf-8").strip()
    description = "Pazo Guillermo. Estudiante de Ingeniería de Sistemas."
    write_svg("inicio", 880, 308, description, f'''
<defs>
  <clipPath id="panel"><rect x="1" y="1" width="878" height="306" rx="24"/></clipPath>
</defs>
<g clip-path="url(#panel)">
  <rect x="1" y="1" width="878" height="306" rx="24" fill="{OAT_MILK}"/>
  <path d="M575 1H855a24 24 0 0 1 24 24v258a24 24 0 0 1-24 24H508Z" fill="{FOREST_GREEN}"/>
  <path d="M598 0l-67 308M628 0l-67 308M658 0l-67 308M688 0l-67 308M718 0l-67 308M748 0l-67 308M778 0l-67 308M808 0l-67 308M838 0l-67 308M868 0l-67 308" fill="none" stroke="{OAT_MILK}" stroke-opacity=".16"/>
  <circle cx="714" cy="163" r="122" fill="{FOREST_GREEN}" stroke="{OAT_MILK}" stroke-opacity=".5"/>
  <circle cx="714" cy="163" r="137" fill="none" stroke="{OAT_MILK}" stroke-opacity=".55" stroke-dasharray="3 6"/>
  <path d="M576 56h36m-18-18v36M837 238h26m-13-13v26" fill="none" stroke="{OAT_MILK}" stroke-opacity=".55"/>
  <image class="scan" href="data:image/png;base64,{portrait}" x="533" y="14" width="347" height="323"/>
</g>
<rect x="1" y="1" width="878" height="306" rx="24" fill="none" stroke="{PROFILE_EDGE}"/>
<g class="rise">
  {hero_handle(handle, 40, 40)}
  {hero_name(outlines, 36, 133, 102, 228, 119)}
  <text x="40" y="264" font-size="22" fill="{FOREST_GREEN}">Estudiante de Ingeniería de Sistemas</text>
  <text x="40" y="289" font-size="18" fill="{FOREST_GREEN}">Desarrollo web · Datos e IA · AWS</text>
  <circle cx="482.5" cy="55.5" r="21" fill="{TOMATO_RED}"/>
  <path d="M474 47h17v17m0-17-17 17" fill="none" stroke="{OAT_MILK}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</g>''', extra_style=HERO_STYLE)
    write_svg("inicio-movil", 480, 352, description, f'''
<defs>
  <clipPath id="portrait-frame"><rect x="219" y="12" width="244" height="183" rx="24"/></clipPath>
</defs>
<rect x="1" y="1" width="478" height="350" rx="23" fill="{OAT_MILK}" stroke="{PROFILE_EDGE}"/>
<g clip-path="url(#portrait-frame)">
  <path d="M269 12H463V195H218Z" fill="{FOREST_GREEN}"/>
  <circle cx="352" cy="109" r="75" fill="none" stroke="{OAT_MILK}" stroke-opacity=".5"/>
  <circle cx="352" cy="109" r="85" fill="none" stroke="{OAT_MILK}" stroke-opacity=".55" stroke-dasharray="3 6"/>
  <image class="scan" href="data:image/png;base64,{portrait}" x="240" y="16" width="225" height="179"/>
</g>
<g class="rise">
  {hero_handle(handle, 26, 45)}
  <circle cx="43" cy="111" r="17" fill="{TOMATO_RED}"/>
  <path d="M37 105h12v12m0-12-12 12" fill="none" stroke="{OAT_MILK}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  {hero_name(outlines, 23, 210, 70, 280, 86)}
  <text x="26" y="312" font-size="22" fill="{FOREST_GREEN}">Estudiante de Ingeniería de Sistemas</text>
  <text x="26" y="337" font-size="18" fill="{FOREST_GREEN}">Desarrollo web · Datos e IA · AWS</text>
</g>''', extra_style=HERO_STYLE)


def tile(name, title, detail, icon, delay, *, background=OAT_MILK):
    foreground = FOREST_GREEN if background == OAT_MILK else OAT_MILK
    arrow_background, arrow_ink = (OAT_MILK, TOMATO_RED) if background == TOMATO_RED else (TOMATO_RED, OAT_MILK)
    write_svg(name, 280, 118, f"{title}. {detail}.", f'''
<rect x="1" y="1" width="278" height="116" rx="18" fill="{background}" stroke="{PROFILE_EDGE}"/>
<g class="rise" style="animation-delay:{delay}s">
  <path d="{icon}" fill="none" stroke="{foreground}" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="250" cy="28" r="17" fill="{arrow_background}" stroke="{arrow_ink}"/>
  <path d="M244 22h12v12m0-12-12 12" fill="none" stroke="{arrow_ink}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="19" y="72" class="name" font-size="27" font-weight="bold" fill="{foreground}">{escape(title)}</text>
  <text x="20" y="98" font-size="16" fill="{foreground}">{escape(detail)}</text>
</g>''')


def project(name, title, summary, technology, delay):
    write_svg(name, 880, 83, f"{title}. {summary}. {technology}.", f'''
<rect x="1" y="1" width="878" height="81" rx="16" fill="{OAT_MILK}"/>
<path d="M648 1H863a16 16 0 0 1 16 16v49a16 16 0 0 1-16 16H621Z" fill="{FOREST_GREEN}"/>
<rect x="1" y="1" width="878" height="81" rx="16" fill="none" stroke="{PROFILE_EDGE}"/>
<g class="rise" style="animation-delay:{delay}s">
  <text x="31" y="35" class="name" font-size="25" font-weight="bold" fill="{FOREST_GREEN}">{escape(title)}</text>
  <text x="31" y="62" font-size="18" fill="{FOREST_GREEN}">{escape(summary)}</text>
  <text x="802" y="48" font-size="19" text-anchor="end" fill="{OAT_MILK}">{escape(technology)}</text>
  <circle cx="841" cy="42" r="18" fill="{TOMATO_RED}" stroke="{OAT_MILK}"/>
  <path d="M834 35h14v14m0-14-14 14" fill="none" stroke="{OAT_MILK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</g>''')


def chart_style():
    fonts = (
        ("Instrument Serif", "normal", "Instrument-Serif-Regular"),
        ("Instrument Serif", "italic", "Instrument-Serif-Italic"),
        ("Geist Mono", "normal", "Geist-Mono-Regular"),
    )
    faces = []
    for family, style, filename in fonts:
        binary = (ROOT / "scripts" / "fonts" / f"{filename}.woff").read_bytes()
        data = base64.b64encode(binary).decode("ascii")
        faces.append(
            f"@font-face {{ font-family: '{family}'; font-style: {style}; font-weight: 400; "
            f"src: url(data:font/woff;base64,{data}) format('woff'); }}"
        )
    return "\n".join(faces) + CHART_STYLE


def quantity(number):
    return f"{number:,}".replace(",", ".")


def activity(records, typography):
    first, last = records[0][0], records[-1][0]
    start_week = first - timedelta(days=(first.weekday() + 1) % 7)
    columns = (last - start_week).days // 7 + 1
    step = 808 / columns
    cells = []
    labels = []
    for day, level, _ in records:
        column, row = divmod((day - start_week).days, 7)
        x = 36 + column * step
        if day.day == 1 and column < columns - 1:
            labels.append(f'<text x="{x:.1f}" y="204">{MONTHS[day.month - 1]}</text>')
        animation = f' class="lit" style="animation-delay:{.18 + column * .014:.2f}s"' if level else ""
        cells.append(f'<rect x="{x:.1f}" y="{86 + row * 15}" width="{step - 2.5:.1f}" height="12" rx="2.5" fill="{HEAT[level]}"{animation}/>')

    legends = "".join(
        f'<rect x="{732 + index * 14}" y="53" width="11" height="11" rx="2" fill="{color}"/>'
        for index, color in enumerate(HEAT)
    )
    total = quantity(sum(count for _, _, count in records))
    description = f"Actividad en GitHub. Calendario público del {first:%d/%m/%Y} al {last:%d/%m/%Y}. {total} contribuciones."
    write_svg("actividad", 880, 225, description, f'''
<rect x="1" y="1" width="878" height="223" rx="19" fill="{OAT_MILK}" stroke="{PROFILE_EDGE}"/>
<text x="36" y="57" class="chart-title" font-size="43" fill="{FOREST_GREEN}">Actividad <tspan class="chart-italic" fill="{TOMATO_RED}">en GitHub</tspan></text>
<g class="chart-label" font-size="11" fill="{FOREST_GREEN}">
  <text x="843" y="37" text-anchor="end" letter-spacing=".8">ACTUALIZACIÓN DIARIA</text>
  <text x="688" y="63">Menos</text>
  {legends}<text x="843" y="63" text-anchor="end">Más</text>
  {''.join(labels)}
</g>
{''.join(cells)}''', extra_style=typography)


def monthly_contributions(records, typography):
    last = records[-1][0]
    first_year, first_month_index = divmod(last.year * 12 + last.month - 12, 12)
    first_month = date(first_year, first_month_index + 1, 1)
    window = [(day, count) for day, _, count in records if day >= first_month]
    first = window[0][0]
    months = Counter()
    streak = longest = active = 0
    for day, count in window:
        months[day.year, day.month] += count
        streak = streak + 1 if count else 0
        longest = max(longest, streak)
        active += bool(count)

    total = quantity(sum(months.values()))
    best_month, top = max(months.items(), key=lambda entry: entry[1])
    busiest_day, busiest_count = max(window, key=lambda entry: entry[1])
    step = 553 / len(months)
    bar_width = step - 11
    bars = []
    for index, ((year, month), count) in enumerate(months.items()):
        x = 36 + index * step
        center = x + bar_width / 2
        height = max(3, 130 * count / max(top, 1))
        y = 275 - height
        is_best = count > 0 and (year, month) == best_month
        color = TOMATO_RED if is_best else FOREST_GREEN if count else CHART_RULE
        name = MONTHS[month - 1]
        bars.append(f'<rect class="bar" style="animation-delay:{.22 + index * .045:.2f}s" x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{height:.1f}" rx="{min(4, height / 2):.1f}" fill="{color}"><title>{name} {year}: {quantity(count)}</title></rect>')
        bars.append(f'<text class="chart-label" x="{center:.1f}" y="295" text-anchor="middle" font-size="11" fill="{FOREST_GREEN}">{name}</text>')
        if is_best:
            bars.append(f'<text class="chart-label" x="{center:.1f}" y="{y - 9:.1f}" text-anchor="middle" font-size="12" fill="{TOMATO_RED}">{quantity(top)}</text>')

    period = f"{MONTHS[first.month - 1]} {first.year} – {MONTHS[last.month - 1]} {last.year}"
    if last.day < monthrange(last.year, last.month)[1]:
        period += " · mes actual parcial"
    busiest_label = f"Día más activo · {busiest_day:%d/%m/%Y}" if busiest_count else "Día más activo"
    streak_unit = "día" if longest == 1 else "días"
    description = (
        f"Contribuciones por mes. {total} en los últimos 12 meses del calendario. "
        f"Mejor racha de {longest} {streak_unit}. {active} de {len(window)} días activos. "
        f"{busiest_count} contribuciones en el día más activo."
    )
    write_svg("contribuciones", 880, 334, description, f'''
<rect x="1" y="1" width="878" height="332" rx="19" fill="{OAT_MILK}" stroke="{PROFILE_EDGE}"/>
<text x="36" y="40" class="chart-label" font-size="13" letter-spacing="1" fill="{FOREST_GREEN}">CONTRIBUCIONES POR MES</text>
<text x="36" y="98" class="chart-title" font-size="57" fill="{FOREST_GREEN}">{total} <tspan class="chart-italic" font-size="49">contribuciones</tspan></text>
<path d="M36 276H584M618 33V304M648 116H843M648 202H843" fill="none" stroke="{CHART_RULE}"/>
{''.join(bars)}
<text x="36" y="317" class="chart-label" font-size="11" fill="{FOREST_GREEN}">{period}</text>
<g fill="{FOREST_GREEN}">
  <text x="648" y="77" class="chart-title" font-size="41">{quantity(longest)} <tspan class="chart-italic">{streak_unit}</tspan></text>
  <text x="648" y="101" font-size="15">Mejor racha</text>
  <text x="648" y="165" class="chart-title" font-size="41">{quantity(active)} <tspan class="chart-italic">/ {quantity(len(window))}</tspan></text>
  <text x="648" y="189" font-size="15">Días activos en el periodo</text>
  <text x="648" y="251" class="chart-title" font-size="41" fill="{TOMATO_RED}">{quantity(busiest_count)}</text>
  <text x="648" y="275" font-size="15">{busiest_label}</text>
</g>''', extra_style=typography)
    print(description)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calendar-html", type=Path, help="Lee una copia local del calendario de GitHub.")
    parser.add_argument("--activity-only", action="store_true", help="Actualiza el calendario y las contribuciones por mes.")
    args = parser.parse_args()
    if args.calendar_html:
        source = args.calendar_html.read_text(encoding="utf-8-sig")
    else:
        request = Request(CALENDAR_URL, headers={"Accept-Language": "en-US", "User-Agent": "gpazop-profile-readme/1.0"})
        with urlopen(request, timeout=30) as response:
            source = response.read().decode("utf-8")
    calendar = ContributionCalendar()
    calendar.feed(source)
    CARDS.mkdir(exist_ok=True)
    records = calendar.records()
    typography = chart_style()
    activity(records, typography)
    monthly_contributions(records, typography)
    if args.activity_only:
        return

    hero()
    tile("portafolio", "Portafolio", "Mi web personal",
         "M20 22h29v19H20zM23 34l4-4-4-4m8 8h8", .14, background=TOMATO_RED)
    tile("formacion", "Formación", "AWS · Redes · Soporte",
         "M20 24c8-2 13 0 15 3 3-3 8-5 15-3v18c-7-2-12-1-15 2-2-3-7-4-15-2zm15 3v17", .24, background=FOREST_GREEN)
    tile("repositorios", "Repositorios", "Código en GitHub",
         "M27 25l-8 7 8 7m14-14 8 7-8 7m-4-19-6 24", .34)
    project("fupais", "FuPais", "Seguimiento de estancias y plazos migratorios", "React · Vite", .19)
    project("neurito", "Neurito", "Mascota virtual guiada por una red neuronal", "NumPy · Pygame", .28)
    project("vuelos", "Análisis de vuelos", "Exploración interactiva de retrasos en Nueva York", "Python · Streamlit", .37)


if __name__ == "__main__":
    main()
