# 2025-P3-AI-Personas - Team 1

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Applied Data Science Project

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- Design notes, ADRs, and folder structure reference
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         adsp and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for lint/format tools
│
└── adsp                        <- Source code for use in this project.
    ├── __init__.py             <- Python package bootstrapper
    ├── config.py               <- Shared paths and environment config
    ├── app/                    <- UI-facing services (auth, ingestion, reporting, Q&A)
    ├── fe/                     <- Frontend stubs (chat client, upload UI)
    ├── communication/          <- RPC, cache, and event broker adapters
    ├── core/                   <- Orchestrator, prompt/RAG, persona routing, memory, tool use
    ├── data_pipeline/          <- Data ingestion, transformation, vectorization
    ├── modeling/               <- Training and inference utilities
    ├── monitoring/             <- Evaluation + metrics collection
    ├── storage/                <- Business DB, object store, vector DB shims
    └── utils/                  <- Logging, exceptions, helpers
```

--------


## How to contribute

### **Commit Message and Branch Naming Rules**

1. **Commit Message Format**
    - Use the following format for commit messages:
      ```
      <type>: <short description>
      ```
    - **Types**:
      - `feature` or`feat`: A new feature
      - `fix`: A bug fix
      - `docs`: Documentation changes
      - `chore`: maintenance tasks, repo setup, config, etc.
      - `style`: Code style changes (formatting, missing semicolons, etc.)
      - `refactor`: Code refactoring without adding features or fixing bugs
      - `test`: adding or updating tests.
    - Example:
      ```
      feat: add data preprocessing pipeline
      fix: resolve issue with model training script
      ```
    - Details: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 

2. **Branch Naming Convention**
    - Use the following format for branch names:
      ```
      <type>/<short-description>
      ```
    - **Types**:
      - `main` or `master`: Stable, production-ready code
      - `develop`: Integration branch for features before release (optional)
      - `feature` or `feat`: For new features or enhancements
      - `fix`: For bug fixes
      - `hotfix`: For urgent production fixes
      - `chore`: For maintenance, build, or config tasks
      - `docs`: For documentation-only changes
      - `refactor`: For code refactoring without behavior change
      - `test`: For adding or updating tests
      - `release`: For preparing production releases
    - Example:
     ```
     feat/add-preprocessing-pipeline
     fix/model-training-bug
     ```
    - Details: [Git Branch Naming Convention](https://conventional-branch.github.io/#specification)
    
    - Branch Flow:
    ```
    main <--- release <--- develop <--- feature
     ^                         |
     |                         |
     └-------- hotfix ---------┘
   ```
### **Jupyter Notebook Usage**

1. **Notebook Organization**
    - Notebooks must be stored in the `notebooks/` directory.
    - Naming convention: `PHASE.NOTEBOOK-INITIALS-DESCRIPTION.ipynb`
        
        Example: `0.01-pjb-data-source-1.ipynb`
        
        - `PHASE` codes:
            - `0` – Data exploration
            - `1` – Data cleaning & feature engineering
            - `2` – Visualization
            - `3` – Modeling
            - `4` – Publication
        - `INITIALS` – Your initials; helps identify the author and avoid conflicts.
        - `DESCRIPTION` – Short, clear description of the notebook's purpose.

### **Code Reusability & Refactoring Regulation**

1. **Refactor Shared Code into Modules**
    - Store reusable code in the `src/` package.
    - Add the following cell at the top of each notebook:

    ```python
    %load_ext autoreload
    %autoreload 2
    ```
