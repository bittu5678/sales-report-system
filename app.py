import streamlit as st
import pandas as pd
import datetime
import calendar
import os
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from fpdf import FPDF
import numpy as np
import tempfile

# ───────────────────────────────────────────
# PAGE CONFIG
# ───────────────────────────────────────────
st.set_page_config(
    page_title="Sales Report System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ───────────────────────────────────────────
# CUSTOM CSS
# ───────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #334155;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin: 8px 0;
    }
    .metric-card h2 { color: #38bdf8; font-size: 28px; margin: 0; }
    .metric-card p  { color: #94a3b8; font-size: 13px; margin: 4px 0 0 0; }

    .title-bar {
        background: linear-gradient(90deg, #1d4ed8, #7c3aed);
        color: white;
        padding: 18px 30px;
        border-radius: 12px;
        text-align: center;
        font-size: 26px;
        font-weight: bold;
        letter-spacing: 1px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(29,78,216,0.5);
    }
    .section-header {
        color: #38bdf8;
        font-size: 18px;
        font-weight: bold;
        padding: 8px 0;
        border-bottom: 2px solid #1d4ed8;
        margin-bottom: 16px;
    }
    .success-box {
        background: #052e16;
        border: 1px solid #16a34a;
        border-radius: 8px;
        padding: 16px;
        color: #4ade80;
    }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 44px;
    }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────
# SESSION STATE – in-memory CSV
# ───────────────────────────────────────────
if "sales_data" not in st.session_state:
    # Default sample data
    st.session_state.sales_data = pd.DataFrame([
        {"Date": "2024-01-05", "Employee": "Aman",  "Sales": 12000},
        {"Date": "2024-01-10", "Employee": "Riya",  "Sales": 15000},
        {"Date": "2024-02-02", "Employee": "Mohit", "Sales": 10000},
        {"Date": "2024-02-15", "Employee": "Neha",  "Sales": 18000},
        {"Date": "2024-03-01", "Employee": "Rahul", "Sales": 22000},
        {"Date": "2024-03-10", "Employee": "Priya", "Sales": 17000},
    ])
    st.session_state.sales_data["Date"] = pd.to_datetime(st.session_state.sales_data["Date"])

# ───────────────────────────────────────────
# REPORT GENERATION FUNCTION
# ───────────────────────────────────────────
def generate_report_bytes(month: int) -> bytes:
    df = st.session_state.sales_data.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    year = int(df["Date"].dt.year.mode()[0])
    start = datetime.datetime(year, month, 1)
    end   = datetime.datetime(year, month, calendar.monthrange(year, month)[1])
    df = df[(df["Date"] >= start) & (df["Date"] <= end)]

    if df.empty:
        raise ValueError("Is mahine ka koi data nahi mila. Pehle data add karein.")

    summary      = df.groupby("Employee")["Sales"].sum().reset_index()
    total_sales  = summary["Sales"].sum()
    avg_sales    = summary["Sales"].mean()
    max_sales    = summary["Sales"].max()
    min_sales    = summary["Sales"].min()
    top_performer = summary.loc[summary["Sales"].idxmax(), "Employee"]

    def perf(s):
        if s > avg_sales * 1.2: return "Excellent"
        if s > avg_sales:        return "Good"
        return "Needs Improvement"
    summary["Performance"] = summary["Sales"].apply(perf)

    # Previous month
    pm = month - 1 if month > 1 else 12
    py = year if month > 1 else year - 1
    prev_df = st.session_state.sales_data.copy()
    prev_df["Date"] = pd.to_datetime(prev_df["Date"])
    ps = datetime.datetime(py, pm, 1)
    pe = datetime.datetime(py, pm, calendar.monthrange(py, pm)[1])
    prev_df = prev_df[(prev_df["Date"] >= ps) & (prev_df["Date"] <= pe)]
    prev_total = prev_df.groupby("Employee")["Sales"].sum().sum() if not prev_df.empty else 0
    growth = ((total_sales - prev_total) / prev_total * 100) if prev_total > 0 else 0

    # ── Charts ──
    color_map = {"Excellent": "green", "Good": "orange", "Needs Improvement": "red"}
    bar_colors = [color_map[p] for p in summary["Performance"]]

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.patch.set_facecolor("#1e293b")
    for ax in axes.flat:
        ax.set_facecolor("#0f172a")
        ax.tick_params(colors="white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#334155")

    # Bar
    bars = axes[0,0].bar(summary["Employee"], summary["Sales"], color=bar_colors, edgecolor="#334155")
    axes[0,0].set_title(f"Sales Performance – {calendar.month_name[month]} {year}")
    axes[0,0].set_xlabel("Employee", color="white"); axes[0,0].set_ylabel("Sales (Rs.)", color="white")
    axes[0,0].tick_params(axis='x', rotation=30)
    for bar in bars:
        h = bar.get_height()
        axes[0,0].text(bar.get_x() + bar.get_width()/2, h + max_sales*0.01,
                       f'₹{int(h):,}', ha='center', va='bottom', color='white', fontsize=8)

    # Pie
    axes[0,1].pie(summary["Sales"], labels=summary["Employee"], autopct='%1.1f%%',
                  startangle=90, textprops={'color':'white','fontsize':9})
    axes[0,1].set_title("Sales Contribution %")

    # Daily trend
    df["Day"] = df["Date"].dt.day
    daily = df.groupby("Day")["Sales"].sum()
    axes[1,0].plot(daily.index, daily.values, marker='o', color='#38bdf8', linewidth=2)
    axes[1,0].fill_between(daily.index, daily.values, alpha=0.3, color='#38bdf8')
    axes[1,0].set_title("Daily Sales Trend")
    axes[1,0].set_xlabel("Day", color='white'); axes[1,0].set_ylabel("Sales (Rs.)", color='white')
    axes[1,0].grid(True, alpha=0.2)

    # Performance dist
    pc = summary["Performance"].value_counts()
    pc_colors = [color_map[k] for k in pc.index]
    axes[1,1].bar(pc.index, pc.values, color=pc_colors, edgecolor="#334155")
    axes[1,1].set_title("Performance Distribution")
    axes[1,1].set_xlabel("Level", color='white'); axes[1,1].set_ylabel("Employees", color='white')

    plt.tight_layout()

    chart_buf = io.BytesIO()
    plt.savefig(chart_buf, format="png", dpi=150, bbox_inches='tight', facecolor="#1e293b")
    plt.close()
    chart_buf.seek(0)

    # ── PDF ──
    class SalesPDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.set_fill_color(44, 62, 80)
            self.set_text_color(255, 255, 255)
            self.cell(0, 15, 'MONTHLY SALES REPORT', ln=1, align='C', fill=True)
            self.set_text_color(0, 0, 0)
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Generated on {datetime.datetime.now().strftime("%d-%b-%Y %H:%M")} | Page {self.page_no()}', 0, 0, 'C')

        def section(self, title):
            self.set_font('Arial', 'B', 12)
            self.set_fill_color(230, 230, 230)
            self.cell(0, 8, title, ln=1, fill=True)
            self.ln(3)

    pdf = SalesPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)

    # Executive Summary
    pdf.section("EXECUTIVE SUMMARY")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 8, f"Month: {calendar.month_name[month]} {year}", ln=True, align='C')
    pdf.ln(4)

    metrics = [
        ("Total Sales",    f"Rs. {total_sales:,}"),
        ("Average Sales",  f"Rs. {avg_sales:,.0f}"),
        ("Growth %",       f"{growth:+.1f}%"),
        ("Top Performer",  top_performer),
        ("Best Sales",     f"Rs. {max_sales:,}"),
        ("Lowest Sales",   f"Rs. {min_sales:,}"),
    ]
    pdf.set_font("Arial", size=10)
    for label, value in metrics:
        pdf.cell(60, 7, label, border=1)
        pdf.cell(60, 7, value, border=1, ln=1)
    pdf.ln(8)

    # Performance Table
    pdf.section("PERFORMANCE ANALYSIS")
    pdf.set_font("Arial", "B", 11)
    for col, w in [("Employee", 70), ("Sales (Rs.)", 50), ("Vs Avg", 40), ("Rating", 30)]:
        pdf.cell(w, 10, col, border=1, align='C')
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for _, row in summary.sort_values("Sales", ascending=False).iterrows():
        diff = (row["Sales"] - avg_sales) / avg_sales * 100
        pdf.cell(70, 8, row["Employee"], border=1)
        pdf.cell(50, 8, f"Rs. {row['Sales']:,}", border=1, align='R')
        pdf.cell(40, 8, f"{diff:+.1f}%", border=1, align='R')
        pdf.cell(30, 8, row["Performance"], border=1, align='C', ln=1)
    pdf.ln(8)

    # MoM Comparison
    pdf.section("MONTH-OVER-MONTH COMPARISON")
    pdf.set_font("Arial", size=10)
    if prev_total > 0:
        pdf.cell(0, 6, f"Previous Month ({calendar.month_name[pm]} {py}): Rs. {prev_total:,}", ln=1)
        pdf.cell(0, 6, f"Current Month  ({calendar.month_name[month]} {year}): Rs. {total_sales:,}", ln=1)
        g_label = f"Increase of {abs(growth):.1f}%" if growth >= 0 else f"Decrease of {abs(growth):.1f}%"
        if growth >= 0: pdf.set_text_color(0, 100, 0)
        else:           pdf.set_text_color(200, 0, 0)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, g_label, ln=1)
        pdf.set_text_color(0, 0, 0)
    else:
        pdf.cell(0, 8, "No previous month data available.", ln=1)
    pdf.ln(5)

    # Charts
    pdf.section("VISUAL ANALYTICS")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(chart_buf.read())
        tmp_path = tmp.name
    pdf.image(tmp_path, x=10, w=190)
    os.unlink(tmp_path)

    # Save PDF to bytes
    pdf_buf = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes


# ───────────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:16px 0 8px'>
        <span style='font-size:40px'>📊</span>
        <h2 style='color:#38bdf8; margin:4px 0'>Sales Report System</h2>
        <p style='color:#64748b; font-size:13px'>Automatic Report Generator</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    page = st.radio("Navigation", ["🏠 Dashboard", "📝 Data Entry", "📊 Generate Report"], label_visibility="collapsed")
    st.divider()

    total_records = len(st.session_state.sales_data)
    employees = st.session_state.sales_data["Employee"].nunique() if total_records else 0
    st.markdown(f"**Records in memory:** {total_records}")
    st.markdown(f"**Unique employees:** {employees}")


# ───────────────────────────────────────────
# TITLE BAR
# ───────────────────────────────────────────
st.markdown('<div class="title-bar">📊 SALES REPORT SYSTEM</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════
if page == "🏠 Dashboard":
    df = st.session_state.sales_data.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    c1, c2, c3, c4 = st.columns(4)
    total = df["Sales"].sum() if not df.empty else 0
    emp   = df["Employee"].nunique() if not df.empty else 0
    best  = df.loc[df["Sales"].idxmax(), "Employee"] if not df.empty else "—"
    recs  = len(df)

    for col, icon, val, label in [
        (c1, "💰", f"₹{total:,}", "Total Sales"),
        (c2, "👥", str(emp), "Employees"),
        (c3, "👑", best, "Top Employee"),
        (c4, "📋", str(recs), "Total Records"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <span style="font-size:28px">{icon}</span>
            <h2>{val}</h2>
            <p>{label}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    if not df.empty:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown('<p class="section-header">📈 Monthly Sales Trend</p>', unsafe_allow_html=True)
            monthly = df.groupby(df["Date"].dt.to_period("M"))["Sales"].sum().reset_index()
            monthly["Date"] = monthly["Date"].astype(str)
            st.bar_chart(monthly.set_index("Date")["Sales"])

        with col_r:
            st.markdown('<p class="section-header">👥 Employee-wise Total Sales</p>', unsafe_allow_html=True)
            emp_sales = df.groupby("Employee")["Sales"].sum().sort_values(ascending=False)
            st.bar_chart(emp_sales)
    else:
        st.info("Koi data nahi hai. Pehle 'Data Entry' mein data add karein.")


# ═══════════════════════════════════════════
# PAGE: DATA ENTRY
# ═══════════════════════════════════════════
elif page == "📝 Data Entry":
    st.markdown('<p class="section-header">📝 Sales Data Entry</p>', unsafe_allow_html=True)

    # ── Upload CSV ──
    with st.expander("📂 Pehle se bana CSV upload karein"):
        uploaded = st.file_uploader("CSV file choose karein", type=["csv"])
        if uploaded:
            try:
                new_df = pd.read_csv(uploaded)
                new_df["Date"] = pd.to_datetime(new_df["Date"])
                st.session_state.sales_data = new_df
                st.success(f"✅ {len(new_df)} records load ho gaye!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")

    # ── Add Entry Form ──
    st.markdown("**➕ Naya Entry Add Karein**")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        entry_date = st.date_input("Date", value=datetime.date.today())
    with col2:
        employee = st.selectbox("Employee", ["Aman", "Riya", "Mohit", "Neha", "Rahul", "Priya", "Other"])
        if employee == "Other":
            employee = st.text_input("Employee ka naam likhein")
    with col3:
        sales_amt = st.number_input("Sales Amount (Rs.)", min_value=0, step=500, value=10000)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add", use_container_width=True):
            if employee and sales_amt > 0:
                new_row = pd.DataFrame([{
                    "Date": pd.to_datetime(entry_date),
                    "Employee": employee,
                    "Sales": sales_amt
                }])
                st.session_state.sales_data = pd.concat([st.session_state.sales_data, new_row], ignore_index=True)
                st.success(f"✅ Entry add ho gayi: {employee} – ₹{sales_amt:,}")
                st.rerun()
            else:
                st.warning("Kripya sab fields bharein.")

    st.markdown("---")

    # ── Data Table ──
    df_show = st.session_state.sales_data.copy()
    df_show["Date"] = df_show["Date"].dt.strftime("%Y-%m-%d")
    df_show["Sales"] = df_show["Sales"].apply(lambda x: f"₹{int(x):,}")

    st.markdown(f'<p class="section-header">📋 Current Data ({len(df_show)} records)</p>', unsafe_allow_html=True)
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)
    with col_a:
        # Download current data as CSV
        csv_bytes = st.session_state.sales_data.to_csv(index=False).encode()
        st.download_button("💾 CSV Download Karein", data=csv_bytes,
                           file_name="sales_data.csv", mime="text/csv",
                           use_container_width=True)
    with col_b:
        if st.button("🗑️ Saara Data Clear Karein", use_container_width=True):
            st.session_state.sales_data = pd.DataFrame(columns=["Date", "Employee", "Sales"])
            st.rerun()


# ═══════════════════════════════════════════
# PAGE: GENERATE REPORT
# ═══════════════════════════════════════════
elif page == "📊 Generate Report":
    st.markdown('<p class="section-header">📊 Report Generator</p>', unsafe_allow_html=True)

    df = st.session_state.sales_data.copy()
    if df.empty:
        st.warning("⚠️ Pehle Data Entry mein data add karein.")
        st.stop()

    df["Date"] = pd.to_datetime(df["Date"])
    available_months = df["Date"].dt.month.unique()
    month_names = {i: calendar.month_name[i] for i in range(1, 13)}

    col1, col2 = st.columns([2, 1])
    with col1:
        month_label = st.selectbox(
            "📅 Month Select Karein",
            options=sorted(available_months),
            format_func=lambda m: month_names[m]
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("🚀 Report Generate Karein", use_container_width=True)

    st.markdown("---")

    # ── Preview ──
    month_df = df[df["Date"].dt.month == month_label]
    if not month_df.empty:
        summary = month_df.groupby("Employee")["Sales"].sum().reset_index()
        avg = summary["Sales"].mean()

        st.markdown(f"**Preview – {month_names[month_label]}**")
        pc = st.columns(3)
        pc[0].metric("Total Sales", f"₹{month_df['Sales'].sum():,}")
        pc[1].metric("Employees",   month_df["Employee"].nunique())
        pc[2].metric("Top Performer", summary.loc[summary["Sales"].idxmax(), "Employee"])

        st.dataframe(
            summary.assign(
                Sales=summary["Sales"].apply(lambda x: f"₹{int(x):,}"),
                Performance=summary["Sales"].apply(
                    lambda s: "🟢 Excellent" if s > avg*1.2 else ("🟡 Good" if s > avg else "🔴 Needs Improvement")
                )
            ),
            use_container_width=True, hide_index=True
        )

    # ── Generate ──
    if generate_btn:
        with st.spinner("Report generate ho rahi hai..."):
            try:
                pdf_bytes = generate_report_bytes(month_label)
                year_val = int(df["Date"].dt.year.mode()[0])
                filename = f"Sales_Report_{month_names[month_label]}_{year_val}.pdf"

                st.markdown("""
                <div class="success-box">
                    ✅ <strong>Report successfully generate ho gayi!</strong><br>
                    Neeche download button se PDF download karein.
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    label="📥 PDF Report Download Karein",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Error: {e}")
