&#x20;ChurnGuard AI



&#x20;An Open-Source Statistical Framework for Customer Retention Analysis Using Python



<p align="center">

&#x20; <b>Customer Analytics · RFM Segmentation · Statistical Computing · Data Visualisation</b>

</p>



ChurnGuard AI is a Python-based customer retention analysis framework designed to investigate customer purchasing behaviour, identify inactivity patterns, and explore relationships between historical purchasing activity and future customer behaviour.



The project combines customer-level RFM analysis, transparent heuristic risk scoring, statistical evaluation, and interactive visualisation.



\*\*Research proposal:\*\* Submitted to SciPy India 2026 as a poster proposal.



> \*\*Development status:\*\* Initial data engineering pipeline and 18 automated tests completed. Standalone scoring equivalence, statistical analysis, sensitivity testing, and final dashboard integration remain under development.



\---



1\. Project Overview



Customer retention is an important challenge for businesses operating in competitive markets.



ChurnGuard explores how historical purchasing behaviour can help identify customers who may become inactive.



Rather than treating a heuristic score as a machine-learning prediction, the framework separates:



\* Historical customer behaviour.

\* Rule-based risk indicators.

\* Observed future inactivity.

\* Statistical associations.

\* Predictive performance evaluation.



The primary objective is to create a transparent and reproducible statistical framework using Python and the scientific computing ecosystem.



2\. System Architecture



The project follows a modular architecture that separates data preparation, feature engineering, analysis, and presentation.



```mermaid

flowchart TD

&#x20;   A\["UCI Online Retail Dataset"] --> B\["Data Ingestion"]

&#x20;   B --> C\["Data Cleaning"]

&#x20;   C --> D\["Data Quality Audit"]

&#x20;   D --> E\["Customer-Level Feature Engineering"]

&#x20;   E --> F\["RFM Feature Dataset"]



&#x20;   F --> G\["Heuristic Risk Scoring"]

&#x20;   F --> H\["Statistical Analysis"]



&#x20;   G --> I\["Customer Risk Categories"]

&#x20;   H --> J\["Statistical Findings"]



&#x20;   I --> K\["Streamlit Dashboard"]

&#x20;   J --> K



&#x20;   K --> L\["Interactive Customer Analytics"]

&#x20;   K --> M\["Retention Insights"]

&#x20;   K --> N\["Visual Exploration"]



&#x20;   style A fill:#243447,color:#fff

&#x20;   style F fill:#285943,color:#fff

&#x20;   style K fill:#34495e,color:#fff

```



Core Components



| Component            | Responsibility                                     |

| -------------------- | -------------------------------------------------- |

| Data Pipeline        | Cleaning and validating transaction data           |

| Feature Engineering  | Creating customer-level RFM features               |

| Heuristic Scoring    | Calculating transparent risk indicators            |

| Statistical Analysis | Testing relationships and estimating effect sizes  |

| Dashboard            | Interactive customer exploration and visualisation |



3\. Data Processing Pipeline



ChurnGuard uses the UCI Online Retail dataset.



The original dataset contains 541,909 transaction records covering December 2010 to December 2011.



The preprocessing pipeline applies documented cleaning and exclusion rules.



```mermaid

flowchart TD

&#x20;   A\["Raw Transactions<br/>541,909 rows"] --> B\["Remove Missing Customer IDs"]

&#x20;   B --> C\["Exclude Cancellation Invoices"]

&#x20;   C --> D\["Filter Invalid Prices"]

&#x20;   D --> E\["Exclude Non-Product Transactions"]

&#x20;   E --> F\["Retain Eligible Transaction Records"]

&#x20;   F --> G\["Customer-Level Aggregation"]

&#x20;   G --> H\["RFM Feature Engineering"]

&#x20;   H --> I\["Historical Inactivity Labelling"]

&#x20;   I --> J\["Processed Customer Dataset"]



&#x20;   style A fill:#34495e,color:#fff

&#x20;   style F fill:#285943,color:#fff

&#x20;   style J fill:#285943,color:#fff

```



Initial Data Audit



| Metric                                |  Result |

| ------------------------------------- | ------: |

| Raw transaction records               | 541,909 |

| Missing CustomerID records            | 135,080 |

| Records after missing-ID exclusion    | 406,829 |

| Cancellation invoice records excluded |   8,905 |

| Invalid-price records excluded        |      40 |

| Non-product records excluded          |   1,544 |

| Remaining valid transaction records   | 396,340 |

| Valid customers                       |   4,334 |



These figures describe the initial cleaning pipeline. The audit reports preserve the exclusion counts.



Data quality considerations:



\* Missing customer identifiers prevent customer-level attribution.

\* Cancellation invoices are excluded from eligible purchases.

\* Invalid prices are excluded.

\* Non-product transaction codes are handled separately.

\* Duplicate records are audited rather than silently discarded.



Approximately £1.76 million in positive sales associated with missing customer identifiers is not represented in customer-level RFM analysis. This is an important limitation.



4\. RFM Feature Engineering



RFM analysis represents customer purchasing behaviour through three features.



```mermaid

flowchart LR

&#x20;   A\["Customer Transactions"] --> B\["Recency"]

&#x20;   A --> C\["Frequency"]

&#x20;   A --> D\["Monetary"]



&#x20;   B --> E\["Customer RFM Profile"]

&#x20;   C --> E

&#x20;   D --> E



&#x20;   E --> F\["Customer Segmentation"]

&#x20;   E --> G\["Risk Scoring"]

```



Feature Definitions



| Feature   | Definition                                              |

| --------- | ------------------------------------------------------- |

| Recency   | Days since the customer's most recent eligible purchase |

| Frequency | Number of distinct purchase invoices                    |

| Monetary  | Total eligible purchase value                           |



The analysis uses GBP (£) as the transaction currency.



5\. Historical Evaluation Framework



An important design decision is the separation of historical customer features from future inactivity outcomes.



This helps prevent temporal data leakage.



Evaluation Configuration



| Parameter         | Configuration                               |

| ----------------- | ------------------------------------------- |

| Historical cutoff | 9 September 2011                            |

| Outcome window    | 10 September – 8 December 2011              |

| Outcome duration  | 90 complete days                            |

| Inactivity proxy  | No valid purchase during the outcome window |



```mermaid

flowchart TD

&#x20;   A\["Complete Transaction History"] --> B\["Historical Cutoff<br/>9 September 2011"]



&#x20;   B --> C\["Historical Data"]

&#x20;   B --> D\["Future Outcome Window"]



&#x20;   C --> E\["Calculate RFM Features"]

&#x20;   C --> F\["Calculate Heuristic Risk Score"]



&#x20;   D --> G\["Observe Future Purchases"]

&#x20;   G --> H\["Determine Inactivity Outcome"]



&#x20;   E --> I\["Customer-Level Analysis"]

&#x20;   F --> I

&#x20;   H --> I



&#x20;   style C fill:#285943,color:#fff

&#x20;   style D fill:#34495e,color:#fff

```



A customer is labelled inactive when they have no valid purchase in the subsequent 90-day window.



Important: This is an operational inactivity proxy, not proof of permanent customer churn.



Initial Cohort Results



| Metric                           | Result |

| -------------------------------- | -----: |

| Eligible customers               |  3,368 |

| Customers classified as inactive |  1,451 |

| Observed inactivity rate         |  43.1% |



Customers first appearing after the historical cutoff are excluded from the evaluation cohort because they do not have historical purchasing information at the cutoff.



6\. Heuristic Risk Scoring



The existing dashboard uses a transparent rule-based scoring approach.



The score combines three components:



```mermaid

flowchart TD

&#x20;   A\["Customer RFM Features"] --> B\["Recency Component"]

&#x20;   A --> C\["Frequency Component"]

&#x20;   A --> D\["Monetary Component"]



&#x20;   B --> E\["65% Weight"]

&#x20;   C --> F\["20% Weight"]

&#x20;   D --> G\["15% Weight"]



&#x20;   E --> H\["Combined Heuristic Score"]

&#x20;   F --> H

&#x20;   G --> H



&#x20;   H --> I\["Risk Categorisation"]

&#x20;   I --> J\["Low Risk"]

&#x20;   I --> K\["Medium Risk"]

&#x20;   I --> L\["High Risk"]

```



| Component | Weight |

| --------- | -----: |

| Recency   |    65% |

| Frequency |    20% |

| Monetary  |    15% |



The scoring system uses percentile-based scaling for frequency and monetary values and a configurable inactivity threshold for recency.



The dashboard categorises customers into Low, Medium, and High risk groups.



Methodological distinction: This is a heuristic risk indicator. It is not a trained machine-learning model and must not be interpreted as a calibrated churn probability.



7\. Statistical Analysis Framework



The research component investigates whether customer purchasing behaviour differs between customers who remain active and those who become inactive during the outcome window.



Planned Statistical Methods



| Method               | Research purpose                                                |

| -------------------- | --------------------------------------------------------------- |

| Mann–Whitney U       | Compare RFM distributions between active and inactive customers |

| Spearman Correlation | Examine monotonic relationships between customer features       |

| Chi-square Test      | Examine associations between categorical variables              |

| Kruskal–Wallis       | Compare outcome distributions across customer segments          |

| Bootstrap            | Estimate confidence intervals                                   |

| Sensitivity Analysis | Examine robustness under alternative analytical configurations  |



Statistical Workflow



```mermaid

flowchart TD

&#x20;   A\["Customer-Level Dataset"] --> B\["Exploratory Data Analysis"]



&#x20;   B --> C\["Define Research Hypotheses"]



&#x20;   C --> D\["Select Statistical Tests"]



&#x20;   D --> E\["Calculate Test Statistics"]



&#x20;   E --> F\["Estimate Effect Sizes"]



&#x20;   F --> G\["Bootstrap Confidence Intervals"]



&#x20;   G --> H\["Multiple Testing Correction"]



&#x20;   H --> I\["Sensitivity Analysis"]



&#x20;   I --> J\["Interpret Findings"]

```



The planned primary analysis includes six hypotheses, with Holm correction across the six primary tests.



Pairwise post-hoc comparisons will use a separate multiple-testing correction family.



Effect sizes and confidence intervals will accompany statistical significance wherever appropriate.



Status: This statistical module is not yet complete. The methods above describe the planned analysis, not completed research findings.



8\. Interactive Dashboard



The project includes a Streamlit dashboard designed to make customer analytics easier to explore.



Dashboard Modules



| Module             | Purpose                               |

| ------------------ | ------------------------------------- |

| Overview           | High-level customer analytics         |

| Customer Explorer  | Explore individual customer behaviour |

| Retention Playbook | Review retention recommendations      |

| Profile            | Customer profile functionality        |

| About              | Project information                   |



Technology Stack



\* Python

\* Pandas

\* NumPy

\* SciPy

\* Streamlit

\* Plotly

\* OpenPyXL



9\. Repository Structure



```text

ChurnGuard-AI/

│

├── churnguard/

│   ├── \_\_init\_\_.py

│   ├── config.py

│   ├── data\_pipeline.py

│   ├── features.py

│   └── build\_dataset.py

│

├── tests/

│   ├── \_\_init\_\_.py

│   └── test\_pipeline.py

│

├── data/

│   ├── raw/

│   └── processed/

│

├── churnguard\_scipy\_redesign.py

├── requirements\_voice.txt

├── .gitignore

└── README.md

```



Raw data, generated customer-level datasets, virtual environments, and local backups are intentionally excluded from version control.



10\. Installation and Setup



Step 1: Clone the repository



```bash

git clone https://github.com/akshaykumarj952-commits/ChurnGuard-AI.git



cd ChurnGuard-AI

```



Step 2: Create a virtual environment



```bash

python -m venv .venv

```



Activate it on Windows:



```powershell

.venv\\Scripts\\Activate.ps1

```



Step 3: Install dependencies



```bash

pip install -r requirements\_voice.txt

pip install scipy openpyxl

```



Step 4: Download the dataset



Download the Online Retail dataset from:



https://archive.ics.uci.edu/dataset/352/online+retail



Place the downloaded Excel file at:



```text

data/raw/Online Retail.xlsx

```



Step 5: Build the processed dataset



```bash

python -m churnguard.build\_dataset

```



The pipeline generates:



\* `data/processed/customers\_features.csv`

\* `data/processed/data\_audit.json`

\* `data/processed/data\_audit.md`



The generated customer-level CSV is excluded from Git version control.



Step 6: Run the dashboard



```bash

python -m streamlit run churnguard\_scipy\_redesign.py

```



Step 7: Run automated tests



```bash

python -m unittest tests.test\_pipeline -v

```



The initial pipeline test suite contains 18 tests covering synthetic and real-data scenarios.



11\. Reproducibility and Data Protection



ChurnGuard is designed to keep analytical outputs separate from private input data.



Important practices include:



\* Documented preprocessing rules.

\* Fixed historical evaluation cutoff.

\* Separation of historical features and future outcomes.

\* Automated pipeline tests.

\* Duplicate transaction auditing.

\* Explicit exclusion reporting.

\* Customer-level data excluded from the public repository.



12\. Limitations



The current research has several limitations:



1\. The dataset represents a single online retail business.

2\. Customer identifiers are missing for a substantial proportion of transactions.

3\. The inactivity definition is based on a fixed 90-day observation window.

4\. The evaluation period includes seasonal purchasing effects.

5\. The current risk score is heuristic rather than model-trained.

6\. RFM segments and risk categories partly depend on recency, so some statistical relationships are structurally expected.

7\. Statistical validation and sensitivity analyses are still in development.



13\. Development Roadmap



```mermaid

flowchart TD

&#x20;   A\["Phase 1<br/>Data Acquisition"] --> B\["Phase 2<br/>Data Cleaning"]

&#x20;   B --> C\["Phase 3<br/>Feature Engineering"]

&#x20;   C --> D\["Phase 4<br/>Statistical Analysis"]

&#x20;   D --> E\["Phase 5<br/>Validation \& Sensitivity"]

&#x20;   E --> F\["Phase 6<br/>Dashboard Integration"]

&#x20;   F --> G\["Phase 7<br/>Research Poster"]



&#x20;   style A fill:#285943,color:#fff

&#x20;   style B fill:#285943,color:#fff

&#x20;   style C fill:#285943,color:#fff

&#x20;   style D fill:#34495e,color:#fff

&#x20;   style E fill:#34495e,color:#fff

&#x20;   style F fill:#34495e,color:#fff

&#x20;   style G fill:#34495e,color:#fff

```



\* \[x] Initial project structure

\* \[x] Dataset acquisition

\* \[x] Data cleaning pipeline

\* \[x] Customer-level RFM feature engineering

\* \[x] Historical inactivity outcome construction

\* \[x] Initial automated tests

\* \[x] GitHub repository

\* \[ ] Standalone heuristic scoring implementation

\* \[ ] Heuristic equivalence tests

\* \[ ] Statistical hypothesis testing

\* \[ ] Effect-size estimation

\* \[ ] Bootstrap confidence intervals

\* \[ ] Sensitivity analysis

\* \[ ] Dashboard integration

\* \[ ] Research poster



14\. Conference Submission



SciPy India 2026



Proposed poster title:



ChurnGuard: An Open-Source Statistical Framework for Customer Retention Analysis Using Python



The proposal has been submitted. Submission does not imply acceptance or conference endorsement.



15\. Dataset Citation and Acknowledgements



Chen, D. (2015). \*Online Retail\* \[Dataset]. UCI Machine Learning Repository.



https://doi.org/10.24432/C5BW33



Dataset licence: Creative Commons Attribution 4.0 International (CC BY 4.0).



The dataset is provided by the UCI Machine Learning Repository. Its original attribution and licence must be preserved when using or redistributing the data.



16\. Author



&#x20; Akshay Kumar Jha



Student | Python | Data Analytics | Statistical Computing



GitHub: https://github.com/akshaykumarj952-commits



\---



<p align="center">

&#x20; <b>ChurnGuard AI</b><br>

&#x20; Building transparent and reproducible customer analytics with Python.

</p>



