"""
report_generator.py
-------------------
Convierte el reporte del analyzer en formatos listos para enviar:
  - Texto Markdown (Telegram)
  - HTML completo (archivo histórico)
"""

from datetime import datetime
from typing import Dict
import pytz

ART = pytz.timezone("America/Argentina/Buenos_Aires")

SIGNAL_EMOJI = {
    "BUY":   "🟢",
    "HOLD":  "🟡",
    "SELL":  "🔴",
    "AVOID": "⛔",
}


class ReportGenerator:

    # ------------------------------------------------------------------
    # Telegram (Markdown)
    # ------------------------------------------------------------------

    def telegram_message(self, report: Dict) -> str:
        date_str, time_str = self._split_ts(report["analysis_date"])
        top_3   = report["top_3"]
        alerts  = report["alerts"]
        summary = report["summary"]

        lines = [
            "📊 *ANÁLISIS FUNDAMENTAL MERVAL*",
            f"📅 {date_str}  🕗 {time_str} ART",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🏆 *TOP 3 OPORTUNIDADES*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        for opp in top_3:
            em = SIGNAL_EMOJI.get(opp["signal"], "")
            lines += [
                "",
                f"{opp['rank']}\\. *{opp['ticker']}* — {opp['sector']}",
                f"   {em} Señal: *{opp['signal']}*",
                f"   💰 Precio: ${opp['price_usd']}  •  Market Cap: ${opp['market_cap_b']}B",
                f"   📐 P/BV: {opp['p_bv']}x  •  P/E: {opp['p_e']}x  •  ROE: {opp['roe']}",
                f"   💡 _{opp['rationale']}_",
            ]

        lines += ["", "━━━━━━━━━━━━━━━━━━━━━━━━━"]

        if alerts:
            lines += ["⚠️ *ALERTAS*", ""]
            for a in alerts:
                lines.append(a)
            lines.append("")

        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📈 *RESUMEN DEL PANEL*",
            f"Total: {summary['total']} acciones  •  "
            f"🟢 {summary['buy']} BUY  •  🟡 {summary['hold']} HOLD  •  "
            f"🔴 {summary['sell']} SELL  •  ⛔ {summary['avoid']} AVOID",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            "_Generado automáticamente · MCP AlphaCast + Claude_",
            "_Lun / Mié / Vie · 08:00 ART_",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # HTML (histórico)
    # ------------------------------------------------------------------

    def html_report(self, report: Dict) -> str:
        date_str, time_str = self._split_ts(report["analysis_date"])
        top_3   = report["top_3"]
        matrix  = report["full_matrix"]
        alerts  = report["alerts"]
        summary = report["summary"]

        rows_top3 = ""
        for opp in top_3:
            em = SIGNAL_EMOJI.get(opp["signal"], "")
            rows_top3 += f"""
            <tr>
              <td>{opp['rank']}</td>
              <td><strong>{opp['ticker']}</strong></td>
              <td>{opp['sector']}</td>
              <td>${opp['price_usd']}</td>
              <td>{opp['p_bv']}x</td>
              <td>{opp['roe']}</td>
              <td>{opp['p_e']}x</td>
              <td><span class="sig sig-{opp['signal']}">{em} {opp['signal']}</span></td>
              <td><em>{opp['rationale']}</em></td>
            </tr>"""

        rows_matrix = ""
        for s in matrix:
            em = SIGNAL_EMOJI.get(s["signal"], "")
            rows_matrix += f"""
            <tr>
              <td><strong>{s['ticker']}</strong></td>
              <td>{s['sector']}</td>
              <td>${s['price_usd']}</td>
              <td>{s['p_bv']}x</td>
              <td>{s['roe_pct']}%</td>
              <td>{s['p_e']}x</td>
              <td>{s['ev_ebitda']}x</td>
              <td>${s['market_cap_b']}B</td>
              <td><span class="sig sig-{s['signal']}">{em} {s['signal']}</span></td>
            </tr>"""

        alerts_html = ""
        for a in alerts:
            alerts_html += f'<div class="alert">{a}</div>\n'

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análisis Fundamental Merval · {date_str}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 24px; color: #222; background: #f8f9fa; }}
  h1   {{ color: #1a73e8; margin-bottom: 4px; }}
  .subtitle {{ color: #555; margin-bottom: 24px; }}
  .card {{ background: #fff; border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th    {{ background: #1a73e8; color: #fff; padding: 10px 12px; text-align: left; }}
  td    {{ padding: 9px 12px; border-bottom: 1px solid #eee; }}
  tr:hover td {{ background: #f0f4ff; }}
  .sig       {{ font-weight: bold; padding: 3px 8px; border-radius: 4px; }}
  .sig-BUY   {{ background: #d4edda; color: #155724; }}
  .sig-HOLD  {{ background: #fff3cd; color: #856404; }}
  .sig-SELL  {{ background: #f8d7da; color: #721c24; }}
  .sig-AVOID {{ background: #e2e3e5; color: #383d41; }}
  .alert     {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 14px; margin: 8px 0; border-radius: 4px; }}
  .summary   {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .badge     {{ padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; }}
  .b-buy     {{ background: #d4edda; color: #155724; }}
  .b-hold    {{ background: #fff3cd; color: #856404; }}
  .b-sell    {{ background: #f8d7da; color: #721c24; }}
  .b-avoid   {{ background: #e2e3e5; color: #383d41; }}
  footer     {{ color: #999; font-size: 12px; margin-top: 32px; text-align: center; }}
</style>
</head>
<body>

<h1>📊 Análisis Fundamental · Panel Líder Merval</h1>
<p class="subtitle">📅 {date_str} · 🕗 {time_str} ART · {summary['total']} acciones analizadas</p>

<div class="card">
  <h2>🏆 Top 3 Oportunidades</h2>
  <table>
    <tr><th>#</th><th>Ticker</th><th>Sector</th><th>Precio USD</th>
        <th>P/BV</th><th>ROE</th><th>P/E</th><th>Señal</th><th>Rationale</th></tr>
    {rows_top3}
  </table>
</div>

{"<div class='card'><h2>⚠️ Alertas</h2>" + alerts_html + "</div>" if alerts else ""}

<div class="card">
  <h2>📋 Panel Completo</h2>
  <table>
    <tr><th>Ticker</th><th>Sector</th><th>Precio USD</th>
        <th>P/BV</th><th>ROE %</th><th>P/E</th><th>EV/EBITDA</th>
        <th>Mkt Cap</th><th>Señal</th></tr>
    {rows_matrix}
  </table>
</div>

<div class="card">
  <h2>📈 Resumen de Señales</h2>
  <div class="summary">
    <span class="badge b-buy">🟢 BUY: {summary['buy']}</span>
    <span class="badge b-hold">🟡 HOLD: {summary['hold']}</span>
    <span class="badge b-sell">🔴 SELL: {summary['sell']}</span>
    <span class="badge b-avoid">⛔ AVOID: {summary['avoid']}</span>
  </div>
</div>

<footer>
  Generado automáticamente · MCP AlphaCast + Claude · github.com/GuillermoSiaira/merval-fundamentals
</footer>
</body>
</html>"""

    # ------------------------------------------------------------------

    def _split_ts(self, ts: str):
        """'2026-06-07T08:00:00-03:00' → ('2026-06-07', '08:00')"""
        try:
            dt = datetime.fromisoformat(ts)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except Exception:
            parts = ts.split("T")
            return parts[0], parts[1][:5] if len(parts) > 1 else "??:??"


# --- CLI rápido ---
if __name__ == "__main__":
    import json
    from src.alphacast_client import AlphaCastClient
    from src.analyzer import FundamentalAnalyzer

    raw    = AlphaCastClient(simulation_mode=True).get_panel_data()
    report = FundamentalAnalyzer().generate_report(raw)

    gen = ReportGenerator()
    print(gen.telegram_message(report))
    with open("/tmp/merval_report.html", "w", encoding="utf-8") as f:
        f.write(gen.html_report(report))
    print("\n✅ HTML guardado en /tmp/merval_report.html")
