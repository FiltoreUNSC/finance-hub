"""PDF report generation."""

from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from lib.data import fetch_quote
from lib.paper_trading import account_value, load_paper
from lib.portfolio import load_portfolio
from lib.sentiment import analyze_text, fetch_ticker_news


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="HubTitle", parent=styles["Title"], fontSize=22, spaceAfter=12))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=14, spaceBefore=16, spaceAfter=8))
    styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=14))
    return styles


def _table(data: list[list], col_widths=None) -> Table:
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a1a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#7dd3a0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#111111"), colors.HexColor("#0a0a0a")]),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#333333")),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build_pdf_report(watchlist: list[str], report_type: str = "full") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = _styles()
    story = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    story.append(Paragraph("Finance Hub Report", styles["HubTitle"]))
    story.append(Paragraph(f"Generated {now}", styles["Body"]))
    story.append(Spacer(1, 0.2 * inch))

    # Market overview
    if report_type in ("full", "market"):
        story.append(Paragraph("Market Overview", styles["Section"]))
        indices = [("SPY", "S&P 500"), ("QQQ", "Nasdaq"), ("^VIX", "VIX"), ("BTC-USD", "Bitcoin")]
        rows = [["Index", "Price", "Change %"]]
        for sym, label in indices:
            try:
                q = fetch_quote(sym)
                rows.append([label, f"${q['price']:,.2f}" if q["price"] else "—", f"{q['change_pct']:+.2f}%"])
            except Exception:
                rows.append([label, "—", "—"])
        story.append(_table(rows, [2.5 * inch, 1.5 * inch, 1.2 * inch]))
        story.append(Spacer(1, 0.15 * inch))

    # Watchlist
    if report_type in ("full", "watchlist") and watchlist:
        story.append(Paragraph("Watchlist", styles["Section"]))
        rows = [["Ticker", "Price", "Change %", "Sector"]]
        for sym in watchlist[:15]:
            try:
                q = fetch_quote(sym)
                rows.append([sym, f"${q['price']:.2f}", f"{q['change_pct']:+.2f}%", q.get("sector", "—")])
            except Exception:
                rows.append([sym, "—", "—", "—"])
        story.append(_table(rows))
        story.append(Spacer(1, 0.15 * inch))

    # Real portfolio
    if report_type in ("full", "portfolio"):
        positions = load_portfolio()
        if positions:
            story.append(Paragraph("Portfolio (tracked)", styles["Section"]))
            rows = [["Ticker", "Shares", "Avg cost", "Price", "P/L %"]]
            for pos in positions:
                try:
                    q = fetch_quote(pos["ticker"])
                    price = q["price"] or pos["cost"]
                    pnl_pct = (price - pos["cost"]) / pos["cost"] * 100
                    rows.append([
                        pos["ticker"], f"{pos['shares']}", f"${pos['cost']:.2f}",
                        f"${price:.2f}", f"{pnl_pct:+.1f}%",
                    ])
                except Exception:
                    rows.append([pos["ticker"], f"{pos['shares']}", f"${pos['cost']:.2f}", "—", "—"])
            story.append(_table(rows))
            story.append(Spacer(1, 0.15 * inch))

    # Paper trading
    if report_type in ("full", "paper"):
        acct = load_paper()
        total, _, pos_rows = account_value(acct)
        pnl = total - acct["starting_cash"]
        story.append(Paragraph("Paper Trading", styles["Section"]))
        story.append(Paragraph(
            f"Equity: ${total:,.2f} · Cash: ${acct['cash']:,.2f} · P/L: ${pnl:+,.2f}",
            styles["Body"],
        ))
        if pos_rows:
            rows = [["Ticker", "Shares", "Avg", "Price", "P/L"]]
            for p in pos_rows:
                rows.append([p["Ticker"], f"{p['Shares']}", f"${p['Avg cost']}", f"${p['Price']}", f"${p['P/L']:+,.0f}"])
            story.append(Spacer(1, 0.1 * inch))
            story.append(_table(rows))
        story.append(Spacer(1, 0.15 * inch))

    # Sentiment
    if report_type in ("full", "sentiment") and watchlist:
        story.append(Paragraph("News Sentiment", styles["Section"]))
        for sym in watchlist[:5]:
            articles = fetch_ticker_news(sym, 5)
            if not articles:
                continue
            scores = [analyze_text(a["text"]).score for a in articles]
            avg = sum(scores) / len(scores)
            label = "Bullish" if avg > 0.25 else ("Bearish" if avg < -0.25 else "Neutral")
            story.append(Paragraph(f"<b>{sym}</b> — {label} (avg {avg:+.2f})", styles["Body"]))
            for a in articles[:3]:
                s = analyze_text(a["text"])
                story.append(Paragraph(
                    f"• [{s.label}] {a['title'][:90]}",
                    styles["Body"],
                ))
        story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph(
        "<i>Disclaimer: Not financial advice. Data from Yahoo Finance. For personal use only.</i>",
        styles["Body"],
    ))

    doc.build(story)
    return buf.getvalue()


def render_reports(watchlist: list[str]) -> None:
    import streamlit as st

    st.subheader("PDF Reports")
    st.caption("Export your data as a downloadable PDF")

    report_type = st.selectbox("Report type", [
        ("full", "Full report (everything)"),
        ("market", "Market overview only"),
        ("watchlist", "Watchlist only"),
        ("portfolio", "Portfolio only"),
        ("paper", "Paper trading only"),
        ("sentiment", "Sentiment only"),
    ], format_func=lambda x: x[1], key="rpt_type")

    if st.button("Generate PDF", type="primary", key="gen_pdf"):
        with st.spinner("Building report…"):
            try:
                pdf_bytes = build_pdf_report(watchlist, report_type[0])
                st.session_state.pdf_bytes = pdf_bytes
                st.session_state.pdf_name = f"finance_hub_{report_type[0]}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.success(f"Report ready — {len(pdf_bytes) / 1024:.0f} KB")
            except Exception as e:
                st.error(f"Report failed: {e}")
                st.caption("Run: pip install reportlab")

    if st.session_state.get("pdf_bytes"):
        st.download_button(
            "⬇️ Download PDF",
            data=st.session_state.pdf_bytes,
            file_name=st.session_state.get("pdf_name", "report.pdf"),
            mime="application/pdf",
            key="dl_pdf",
        )