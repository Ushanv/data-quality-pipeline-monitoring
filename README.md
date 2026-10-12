# Data Quality & Pipeline Monitoring System

**An interactive data-quality validation and pipeline monitoring dashboard built with Python, Pandas, Streamlit, Plotly, and SQLite.**

[🚀 Live Application](https://data-quality-pipeline-monitoring-4e6vbfdlfpogvlmiq7gzoe.streamlit.app/) | [💻 GitHub Repository](https://github.com/Ushanv/data-quality-pipeline-monitoring)

---

## 📌 Project Overview

Data quality is an important part of reliable data analytics and data engineering pipelines. Missing values, duplicate records, invalid dates, and incorrect numerical values can affect reporting and downstream analysis.

The **Data Quality & Pipeline Monitoring System** is a Python-based application that automatically validates uploaded CSV datasets against predefined data-quality rules.

The application provides interactive validation results, data-quality scores, record-level error details, downloadable reports, and historical pipeline execution monitoring.

### 🎯 Project Objectives

- Automate common data-quality validation checks.
- Identify incorrect or incomplete records before downstream processing.
- Provide clear validation results and quality scores.
- Maintain a history of pipeline validation executions.
- Visualize data-quality trends through an interactive dashboard.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📂 CSV Upload | Upload and preview sales datasets |
| 🔍 Data Validation | Check duplicates, missing IDs, invalid dates, and negative sales |
| 📊 Quality Score | Calculate the percentage of validation rules passed |
| 🚨 Error Detection | Identify records that violate validation rules |
| 📈 Pipeline Monitoring | Visualize historical validation runs and quality trends |
| 🗄️ SQLite Integration | Store pipeline execution history |
| 📥 Downloadable Reports | Export validation summaries and record-level errors |
| 🌐 Cloud Deployment | Access the application through Streamlit Community Cloud |

---

## 🏗️ System Architecture

The application follows a simple data-validation and monitoring workflow.

```text
          CSV Dataset
               |
               v
       Streamlit Upload
               |
               v
      Pandas Data Processing
               |
               v
       Validation Engine
               |
       +-------+-------+
       |       |       |
   Missing  Duplicate  Invalid
    Values    Rows     Values
       |       |       |
       +-------+-------+
               |
               v
       Validation Results
               |
       +-------+-------+
       |               |
       v               v
   SQLite DB       Quality Score
       |               |
       v               v
 Pipeline History   Streamlit UI
       |               |
       +-------+-------+
               |
               v
      Reports and Charts
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Pandas | CSV processing and data validation |
| Streamlit | Interactive web application |
| Plotly | Data visualization and charts |
| SQLite | Storage of pipeline execution history |
| GitHub | Source code management |
| Streamlit Community Cloud | Application deployment |

---

## 🔎 Data Validation Rules

The application performs four predefined validation checks.

| Validation Rule | Description |
|---|---|
| Duplicate Records | Detects duplicate rows |
| Missing Customer ID | Identifies records with missing customer identifiers |
| Invalid Order Date | Detects invalid or incorrectly formatted dates |
| Invalid Sales Amount | Identifies negative or invalid sales values |

### Data Quality Score

The data-quality score is calculated using the proportion of validation rules that pass.

**Quality Score (%) = (Passed Validation Rules / Total Validation Rules) × 100**

Example:

- Total validation rules: 4
- Passed rules: 3
- Failed rules: 1
- Quality score: 75%

This is a rule-based score rather than a percentage of valid dataset rows.

---

## 📸 Application Screenshots

### 1. Data Validation Dashboard

Upload a CSV dataset, preview its records, and view data-quality metrics.

*Add your actual dashboard screenshot here.*

### 2. Validation Results and Error Details

View failed validation rules and identify the records containing data-quality issues.

*Add your actual record-level validation screenshot here.*

### 3. Pipeline Execution History

Monitor previous validation runs and visualize historical data-quality scores.

*Add your actual pipeline history screenshot here.*

---

## 🧪 Sample Validation Scenarios

The project includes two example testing scenarios.

| Scenario | Total Records | Passed Rules | Failed Rules | Quality Score |
|---|---:|---:|---:|---:|
| Test dataset with quality issues | 8 | 0 | 4 | 0% |
| Clean dataset | 8 | 4 | 0 | 100% |

These scenarios demonstrate how the dashboard responds to different data-quality conditions.

---

## 🚀 Run the Project Locally

### Prerequisites

- Python
- pip
- Git (optional)

### 1. Clone the Repository

```bash
git clone https://github.com/Ushanv/data-quality-pipeline-monitoring.git
```

### 2. Navigate to the Project Directory

```bash
cd data-quality-pipeline-monitoring
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application

```bash
python -m streamlit run app.py
```

The dashboard will usually be available at:

`http://localhost:8501`

---

## 📁 Project Structure

```text
data-quality-pipeline-monitoring/
│
├── app.py
├── requirements.txt
├── README.md
│
└── data_quality.db
    (Created locally at runtime)
```

The SQLite database is created when the application runs. It does not need to be committed to GitHub.

---

## 💡 What I Learned

Through this project, I gained practical experience in:

- Implementing data-quality validation using Python and Pandas.
- Designing reusable rule-based data checks.
- Building interactive dashboards with Streamlit.
- Storing and retrieving pipeline execution history using SQLite.
- Visualizing validation results with Plotly.
- Deploying a Python application to Streamlit Community Cloud.

---

## 🔮 Future Enhancements

- Configurable validation rules for different datasets.
- Automated validation scheduling.
- Email notifications for failed validations.
- Support for additional file formats.
- Persistent cloud database storage.
- Machine-learning-based anomaly detection.

These are planned improvements and are not part of the current implementation.

---

##  🔗 Project Links

**Live Demo:** [https://data-quality-pipeline-monitoring-4e6vbfdlfpogvlmiq7gzoe.streamlit.app/](url)

**GitHub Repository:** https://github.com/Ushanv/data-quality-pipeline-monitoring

---

## 👩‍💻 Author

**Usha N V**

Computer Science Engineering Graduate | Python | SQL | Data Analytics | Data Engineering

[GitHub Profile](https://github.com/Ushanv)
