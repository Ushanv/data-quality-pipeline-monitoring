from pathlib import Path
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# 1. APP CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Data Quality & Pipeline Monitoring",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Data Quality & Pipeline Monitoring")
st.caption("Upload data, validate quality rules, and monitor pipeline runs over time.")

DB_PATH = Path(__file__).resolve().parent / "data_quality.db"

VALIDATION_RULES = [
    "Duplicate rows",
    "Missing customer IDs",
    "Invalid dates",
    "Negative sales",
]


# ---------------------------------------------------------
# 2. DATABASE SETUP AND HELPERS
# ---------------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH, timeout=30)


def initialize_database():
    """Create current tables and migrate older validation table safely."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_run_history (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT,
                total_records INTEGER,
                duplicate_rows INTEGER,
                missing_customer_ids INTEGER,
                invalid_dates INTEGER,
                negative_sales INTEGER,
                quality_score REAL,
                source_file TEXT
            )
            """
        )

        history_columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(pipeline_run_history)"
            ).fetchall()
        }
        if "source_file" not in history_columns:
            conn.execute(
                "ALTER TABLE pipeline_run_history ADD COLUMN source_file TEXT"
            )

        validation_exists = conn.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'validation_results'
            """
        ).fetchone() is not None

        if validation_exists:
            validation_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(validation_results)"
                ).fetchall()
            }
            if "run_id" not in validation_columns:
                legacy_name = "validation_results_legacy"
                legacy_exists = conn.execute(
                    """
                    SELECT 1 FROM sqlite_master
                    WHERE type = 'table' AND name = ?
                    """,
                    (legacy_name,),
                ).fetchone() is not None

                # Preserve any existing backup by using a second backup name if needed.
                if legacy_exists:
                    legacy_name = "validation_results_legacy_old"
                conn.execute(
                    f"ALTER TABLE validation_results RENAME TO {legacy_name}"
                )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                rule TEXT,
                failed_records INTEGER,
                status TEXT,
                FOREIGN KEY (run_id) REFERENCES pipeline_run_history(run_id)
            )
            """
        )

        # Import a legacy summary report into the latest known run, if possible.
        for legacy_name in ("validation_results_legacy", "validation_results_legacy_old"):
            legacy_exists = conn.execute(
                """
                SELECT 1 FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (legacy_name,),
            ).fetchone() is not None
            if legacy_exists:
                latest_run = conn.execute(
                    "SELECT MAX(run_id) FROM pipeline_run_history"
                ).fetchone()[0]
                if latest_run is not None:
                    already_migrated = conn.execute(
                        "SELECT COUNT(*) FROM validation_results WHERE run_id = ?",
                        (latest_run,),
                    ).fetchone()[0]
                    legacy_columns = {
                        row[1]
                        for row in conn.execute(
                            f"PRAGMA table_info({legacy_name})"
                        ).fetchall()
                    }
                    if (
                        already_migrated == 0
                        and {"rule", "failed_records", "status"}.issubset(legacy_columns)
                    ):
                        conn.execute(
                            f"""
                            INSERT INTO validation_results
                                (run_id, rule, failed_records, status)
                            SELECT ?, rule, failed_records, status
                            FROM {legacy_name}
                            """,
                            (latest_run,),
                        )

        conn.commit()


def load_history():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT run_id, run_time, total_records, duplicate_rows,
                   missing_customer_ids, invalid_dates, negative_sales,
                   quality_score, source_file
            FROM pipeline_run_history
            ORDER BY run_id
            """,
            conn,
        )


def load_validation_for_run(run_id):
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT rule, failed_records, status
            FROM validation_results
            WHERE run_id = ?
            ORDER BY result_id
            """,
            conn,
            params=(int(run_id),),
        )


def validate_data(dataframe):
    """Validate required columns and calculate rule-based quality metrics."""
    required_columns = {
        "order_id",
        "customer_id",
        "order_date",
        "sales_amount",
    }
    missing_columns = sorted(required_columns - set(dataframe.columns))
    if missing_columns:
        return None, None, (
            "Your CSV is missing required column(s): "
            + ", ".join(missing_columns)
            + ". Required columns: order_id, customer_id, order_date, sales_amount."
        )

    checked = dataframe.copy()
    checked["order_date"] = pd.to_datetime(checked["order_date"], errors="coerce")
    checked["sales_amount"] = pd.to_numeric(
        checked["sales_amount"], errors="coerce"
    )

    duplicate_count = int(checked.duplicated().sum())
    missing_customer_count = int(
        checked["customer_id"].isna().sum()
        + checked["customer_id"].astype(str).str.strip().eq("").sum()
    )
    invalid_date_count = int(checked["order_date"].isna().sum())
    negative_sales_count = int(
        (checked["sales_amount"].isna() | (checked["sales_amount"] < 0)).sum()
    )

    failed_counts = [
        duplicate_count,
        missing_customer_count,
        invalid_date_count,
        negative_sales_count,
    ]
    report = pd.DataFrame(
        {"rule": VALIDATION_RULES, "failed_records": failed_counts}
    )
    report["status"] = report["failed_records"].apply(
        lambda count: "PASS" if count == 0 else "FAIL"
    )

    passed_rules = int((report["status"] == "PASS").sum())
    quality_score = round((passed_rules / len(VALIDATION_RULES)) * 100, 1)

    metrics = {
        "total_records": int(len(checked)),
        "duplicate_rows": duplicate_count,
        "missing_customer_ids": missing_customer_count,
        "invalid_dates": invalid_date_count,
        "negative_sales": negative_sales_count,
        "quality_score": quality_score,
    }
    return report, metrics, None


def find_record_issues(dataframe):
    """Return one detail row for each detected record-level issue."""
    df = dataframe.copy()
    issues = []

    parsed_dates = pd.to_datetime(df["order_date"], errors="coerce")
    sales = pd.to_numeric(df["sales_amount"], errors="coerce")
    duplicate_mask = df.duplicated(keep="first")

    for pos in range(len(df)):
        row = df.iloc[pos]
        csv_row_number = pos + 2  # Account for the CSV header row.

        if duplicate_mask.iloc[pos]:
            issues.append(
                {
                    "row_number": csv_row_number,
                    "order_id": row["order_id"],
                    "validation_rule": "Duplicate row",
                    "issue": "This row duplicates an earlier record.",
                }
            )

        customer_id = row["customer_id"]
        if pd.isna(customer_id) or str(customer_id).strip() == "":
            issues.append(
                {
                    "row_number": csv_row_number,
                    "order_id": row["order_id"],
                    "validation_rule": "Missing customer ID",
                    "issue": "Customer ID is empty.",
                }
            )

        if pd.isna(parsed_dates.iloc[pos]):
            issues.append(
                {
                    "row_number": csv_row_number,
                    "order_id": row["order_id"],
                    "validation_rule": "Invalid date",
                    "issue": f"Cannot parse order date: {row['order_date']}",
                }
            )

        if pd.isna(sales.iloc[pos]) or sales.iloc[pos] < 0:
            issues.append(
                {
                    "row_number": csv_row_number,
                    "order_id": row["order_id"],
                    "validation_rule": "Invalid sales amount",
                    "issue": f"Sales amount is invalid or negative: {row['sales_amount']}",
                }
            )

    return pd.DataFrame(
        issues,
        columns=["row_number", "order_id", "validation_rule", "issue"],
    )


def save_pipeline_run(metrics, report, source_file):
    """Save the run and its summary validation results to SQLite."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pipeline_run_history (
                run_time, total_records, duplicate_rows, missing_customer_ids,
                invalid_dates, negative_sales, quality_score, source_file
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                metrics["total_records"],
                metrics["duplicate_rows"],
                metrics["missing_customer_ids"],
                metrics["invalid_dates"],
                metrics["negative_sales"],
                metrics["quality_score"],
                source_file,
            ),
        )
        run_id = cursor.lastrowid

        conn.executemany(
            """
            INSERT INTO validation_results (run_id, rule, failed_records, status)
            VALUES (?, ?, ?, ?)
            """,
            [
                (run_id, row.rule, int(row.failed_records), row.status)
                for row in report.itertuples(index=False)
            ],
        )
        conn.commit()
    return run_id


# Create/migrate database tables while preserving existing history.
initialize_database()


# ---------------------------------------------------------
# 3. CSV UPLOAD AND VALIDATION
# ---------------------------------------------------------
st.subheader("Upload Data for Quality Validation")
st.write(
    "Upload a CSV containing `order_id`, `customer_id`, `order_date`, and "
    "`sales_amount`. The `quantity` column is optional."
)

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        st.markdown("**Data preview**")
        st.dataframe(
            uploaded_df.head(10),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"{len(uploaded_df):,} rows · {len(uploaded_df.columns)} columns")

        if st.button("▶ Run Data Quality Validation", type="primary"):
            report, metrics, error_message = validate_data(uploaded_df)

            if error_message:
                st.error(error_message)
            else:
                run_id = save_pipeline_run(metrics, report, uploaded_file.name)
                st.session_state["latest_uploaded_run_id"] = run_id
                st.session_state["latest_uploaded_report"] = report
                st.session_state["latest_uploaded_metrics"] = metrics
                st.session_state["latest_error_details"] = find_record_issues(
                    uploaded_df
                )
                st.success(
                    f"Validation completed and saved as pipeline run #{run_id}."
                )
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not read this CSV file: {exc}")


# ---------------------------------------------------------
# 4. RECORD-LEVEL ERROR DETAILS
# ---------------------------------------------------------
if "latest_error_details" in st.session_state:
    st.divider()
    st.subheader("Record-Level Error Details")
    error_details = st.session_state["latest_error_details"]

    if error_details.empty:
        st.success("No record-level issues found. Your data passed all checks!")
    else:
        st.warning(f"Found {len(error_details)} record-level issue(s).")
        st.dataframe(
            error_details,
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "⬇ Download Record-Level Error Report",
            data=error_details.to_csv(index=False).encode("utf-8"),
            file_name="record_level_errors.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------
# 5. LOAD LATEST DATA AND METRICS
# ---------------------------------------------------------
history = load_history()

if history.empty:
    st.info(
        "No pipeline runs are recorded yet. Upload a CSV and click "
        "'Run Data Quality Validation' to create your first run."
    )
    st.stop()

latest = history.iloc[-1]
latest_run_id = int(latest["run_id"])
validation = load_validation_for_run(latest_run_id)


# ---------------------------------------------------------
# 6. TOP-LEVEL KPI CARDS
# ---------------------------------------------------------
st.divider()
st.subheader("Latest Pipeline Run")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Records Processed", f"{int(latest['total_records']):,}")
col2.metric("Quality Score", f"{float(latest['quality_score']):.1f}%")
col3.metric(
    "Failed Checks",
    int((validation["status"] == "FAIL").sum()) if not validation.empty else 0,
)
failure_findings = int(
    latest["duplicate_rows"]
    + latest["missing_customer_ids"]
    + latest["invalid_dates"]
    + latest["negative_sales"]
)
col4.metric("Failure Findings", failure_findings)

source_file = latest["source_file"]
if pd.isna(source_file) or not source_file:
    source_file = "Notebook / existing pipeline"
st.caption(
    f"Run #{latest_run_id} · {latest['run_time']} · Source: {source_file}"
)


# ---------------------------------------------------------
# 7. VALIDATION RESULTS
# ---------------------------------------------------------
st.divider()
st.subheader("Validation Results")

if not validation.empty:
    left, right = st.columns([1.1, 1])

    with left:
        fig = px.bar(
            validation,
            x="rule",
            y="failed_records",
            color="status",
            title="Failures by Validation Rule",
            labels={
                "rule": "Validation Rule",
                "failed_records": "Failed Records",
                "status": "Status",
            },
            color_discrete_map={"PASS": "#16a34a", "FAIL": "#dc2626"},
        )
        fig.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        status_filter = st.selectbox(
            "Filter validation status",
            ["All", "PASS", "FAIL"],
        )
        filtered = validation.copy()
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇ Download Validation Report (CSV)",
        data=validation.to_csv(index=False).encode("utf-8"),
        file_name=f"validation_report_run_{latest_run_id}.csv",
        mime="text/csv",
    )
else:
    st.warning(
        "No detailed validation checks exist for the latest run. Upload a CSV "
        "and run validation to save detailed results for a run."
    )


# ---------------------------------------------------------
# 8. PIPELINE RUN HISTORY AND CHART
# ---------------------------------------------------------
st.divider()
st.subheader("Pipeline Run History")

history_display = history[
    ["run_id", "run_time", "total_records", "quality_score", "source_file"]
].copy()
st.dataframe(history_display, use_container_width=True, hide_index=True)

if len(history) > 1:
    fig_history = px.line(
        history,
        x="run_id",
        y="quality_score",
        markers=True,
        title="Data Quality Score by Pipeline Run",
        hover_data=["run_time", "total_records", "source_file"],
        labels={
            "run_id": "Pipeline Run ID",
            "quality_score": "Quality Score (%)",
            "run_time": "Run Time",
            "total_records": "Records Processed",
            "source_file": "Source File",
        },
    )
    fig_history.update_yaxes(range=[0, 100])
    st.plotly_chart(fig_history, use_container_width=True)
else:
    st.info(
        "Only one run is recorded. Upload and validate more datasets to compare "
        "quality scores over time."
    )

st.caption("Built with Python, Pandas, SQLite, Streamlit, and Plotly.")
