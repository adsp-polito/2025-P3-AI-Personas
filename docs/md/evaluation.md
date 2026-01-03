# Lavazza AI Personas - Evaluation Guide

**Version:** 1.0  
**Date:** December 2025  
**Purpose:** Focused evaluation framework for critical system components

---

## 1. Introduction

### 1.1 Purpose

This document provides detailed evaluation methodologies for four critical components of the Lavazza AI Personas system:

1. **Persona Extraction Pipeline** - Validates extraction of persona indicators/metrics from PDF documents
2. **Fact Extraction Accuracy** - Ensures fact data is correctly extracted
3. **Retrieval Relevance** - Measures RAG system's ability to retrieve relevant context
4. **Authenticity Evaluation** - Confirms AI personas authentically represent consumer segments

### 1.2 Evaluation Philosophy

Each evaluation follows a structured approach:

- **Clear objectives** - What we are measuring
- **Step-by-step methodology** - How to conduct the evaluation
- **Example data structures** - Concrete formats for test data

---

## 2. Evaluation Overview

### 2.1 Critical Components Priority

| Component            | Criticality | Impact                          | Evaluation Focus                    |
|----------------------|-------------|---------------------------------|-------------------------------------|
| Persona Extraction   | CRITICAL    | Foundation for all persona data | Accuracy, completeness, consistency |
| Fact Extraction      | CRITICAL    | Factual grounding for responses | Numeric accuracy, attribution       |
| RAG Retrieval        | CRITICAL    | Prevents hallucinations         | Relevance, precision, recall        |
| Persona Authenticity | HIGH        | User trust and value            | Segment alignment, consistency      |


## 3. Persona Extraction Pipeline Evaluation

### 3.1 Objective

Verify that persona indicators (categories,statements, metrics) are correctly extracted from source PDF documents.

### 3.2 Methodology

#### Step 1: Create Ground Truth Dataset

**Action:** Manually annotate 20-30 representative PDF pages (focusing on Curious Connoisseur Segmentation).

**Annotation Process:**

1. Select pages covering:
    - Curious Connoisseur persona segment
    - Various indicator types (demographics, behaviors, preferences, values)
    - Different visual styles (infographics, tables, text blocks)

2. For each page, document:
    - Expected personas mentioned
    - Expected indicators with complete taxonomy (domain/category)
    - Expected statements with associated metrics

3. Store annotations in structured JSON format

**Example Ground Truth Structure:**

```json
{
  "page_id": "page_11",
  "data_source": "data/raw/lavazza_segmentation_report.pdf",
  "page_number": 11,
  "ground_truth": {
    "personas": [
      "curious-connoisseurs"
    ],
    "indicators": [
      {
        "indicator_id": "gt_ind_001",
        "persona_id": "curious-connoisseurs",
        "domain": "demographics",
        "category": "age",
        "label": "age_distribution",
        "statements": [
          {
            "label": "45-54 age group",
            "metrics": [
              {
                "value": 24.0,
                "unit": "%",
                "description": "45-65 age group representation"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

#### Step 2: Run Extraction Pipeline

**Action:** Execute persona extraction on the same annotated pages.

#### Step 3: Compare and Compute Metrics

**Action:** Compare system output against ground truth.

**Metrics to Compute:**

1. **Persona Detection Rate**
   ```
   Persona Detection Rate = (Correctly Detected Personas) / (Total Ground Truth Personas)
   ```

2. **Metric Recall**
   ```
   Metrics Recall = (Correctly Metrics) / (Total Ground Truth Metrics)
   ```

3. **Metric Precision**
   ```
   Metrics Precision = (Correct Metrics) / (All Extracted Metrics)
   ```


**Metric Matching Rules**

Only retain **indicators** and **statements** that contain **at least one metric**.

A metric is considered a match with a ground truth metric **if all of the following conditions are satisfied**:

   1. Indicator Match

   An indicator matches the ground truth if the number of shared words between the indicator label (or description) and the ground truth label, divided by the smaller word count, is at least 70%.
   2. Statement Label Match
   
   A statement label matches the ground truth if the number of shared words between the statement label and the ground truth label, divided by the smaller word count, is at least 70%.
   
   3. Value Match
   
   The metric value must match the ground truth value.
   
   4. Unit Match
   
   Units are considered equivalent if they belong to the same synonym group defined below.
   
   **Unit Synonym Mapping**
   
   | Equivalent Units |
   | ---------------- |
   | %, percentage    |
   | index, idx       |
   | €, euro, eur     |
   | $, dollar, usd   |
   | £, pound, gbp    |
   | ¥, yen, jpy      |
   | ₹, rupee, inr    |
   | ₩, won, krw      |
   | ₽, ruble, rub    |
   | ₺, lira, try     |
   | ₫, dong, vnd     |
   | ₱, peso, php     |
   | ₦, naira, ngn    |
   | ₴, hryvnia, uah  |
   | ₡, colon, crc    |
   | ₲, guarani, pyg  |
   | ₵, cedi, ghc     |
   | ₸, tenge, kzt    |
   | ₼, manat, azn    |

**Implementation Notes**

* Normalize text (lowercase, remove punctuation, collapse whitespace) before computing word intersections.
* Apply the 70% threshold consistently across all matching steps.



## 4. Fact Extraction Accuracy Evaluation

### 4.1 Objective

Ensure data (numbers, percentages, ratios) are correctly extracted from PDF charts, tables, and infographics.

### 4.2 Methodology

#### Step 1: Create Ground Truth from Source Data

**Action:** Obtain or create ground truth with known values.

Manually extract and verify statistics from 20-30 test pages (focus on Curious Connoisseurs).

**Example Ground Truth Data Structure:**

```json
{
  "fact_id": "fact_demographics_001",
  "data_source": "data/raw/lavazza_segmentation_report.pdf",
  "page_number": 11,
  "facts": [
    {
      "value": "52%",
      "context": "female percentage in segment"
    },
    {
      "value": "48%",
      "context": "male percentage in segment"
    },
    {
      "value": "20",
      "context": "household size of 1"
    }
  ]
}
```

#### Step 2: Run Fact Extraction Pipeline

**Action:** Extract facts data using the pipeline to get markdown files for each page.

#### Step 3: Compare and Compute Metrics

**Metrics:**

1. **Exact Match Accuracy**
   ```
   Exact Match Accuracy = (Exactly Matching Values) / (Total Ground Truth Values)
   ```

**Note:** A value is considered a match if more than 80% of the words from the ground truth appear in the markdown file.

## 5. Retrieval Relevance Evaluation

### 5.1 Objective

Measure how well the RAG system retrieves relevant persona and fact context for user queries.

### 5.2 Methodology

#### Step 1: Create Query-Relevance Dataset

**Action:** Generate test queries( focus on Curious Connoisseurs).

**Example Test Queries:**

```json
{
  "test_queries": [
    {
      "query_id": "q_001",
      "persona_id": "curious-connoisseurs",
      "query": "What is your age?"
    },
    {
      "query_id": "q_002",
      "persona_id": "curious-connoisseurs",
      "query": "What is your gender?"
    }
  ]
}
```

#### Step 2: Run Retrieval System

**Action:** Execute RAG retrieval for all test queries.

#### Step 3: Manually Label Relevance

For each query, manually label the relevance of retrieved documents.

**Relevance Labels:**

- **1 :**  Related
- **0 :** Unrelated

**Example Relevance Annotation:**

```json
{
  "query_id": "q_001",
  "persona_id": "curious-connoisseurs",
  "query": "What is your age?",
  "relevant_docs": [
    {
      "page_content": "Average age is 47 years old",
      "relevance": 1
    },
    {
      "page_content": "I like to try out new food or drink products",
      "relevance": 0
    }
  ]
}
```

#### Step 4: Compute Retrieval Metrics

**Metrics:**

1. **Precision@K**
   ```
   Precision@K = (Relevant docs in top-K) / K
   ```

2. **Recall@K**
   ```
   Recall@K = (Relevant docs in top-K) / (Total relevant docs)
   ```
**Implementation notes:**

* Set retrieval **top-k = 20** (configable) to ensure high recall.
* Manually review the retrieved chunks and mark those that are relevant.
* Treat **all marked relevant chunks** as the ground-truth recall set.
* Compute **Precision@k** and **Recall@k** for **k = 3, 5, 10, and 20**.

## 6. Authenticity Evaluation

### 6.1 Objective

Ensure AI personas authentically represent their consumer segments through expert validation and consistency testing.

### 6.2 Methodology

#### Step 1: Generate Persona Responses

**Action:** Create a set of test questions and generate persona responses (focus on Curious Connoisseurs).

**Test Question Categories:**

```json
{
  "test_questions": [
    {
      "persona_id": "curious-connoisseurs",
      "query": "What coffee format do you prefer and why?",
      "category": "product_preferences"
    },
    {
      "persona_id": "curious-connoisseurs",
      "query": "What factors influence your coffee purchasing decision?",
      "category": "product_preferences"
    }
  ]
}
```

#### Step 2: Response Generation

Use the system to generate responses for the persona to all test questions.

#### Step 3: Expert Evaluation

**Action:** Have domain experts rate persona authenticity.

*Rating Criteria:*

1. **Authenticity (1-5 scale)**
    - How well does the response reflect the expected persona characteristics?
    - 1 = Not authentic, 5 = Very authentic
2. **Style Alignment**
    - Tone, vocabulary, reasoning depth
    - 1 = Poorly aligned, 5 = Perfectly aligned
3. **Factual Grounding**
    - Are statements factually accurate and well-cited?
    - 1 = No citations/hallucinations, 5 = Well-cited and accurate

**Expert Evaluation Form:**

```json
{
  "test_questions": [
    {
      "persona_id": "curious-connoisseurs",
      "query": "What coffee format do you prefer and why?",
      "category": "product_preferences",
      "response": "I prefer espresso because...",
      "ratings": {
        "authenticity": 3,
        "style_alignment": 4,
        "factual_grounding": 5
      }
    },
    {
      "persona_id": "curious-connoisseurs",
      "query": "What factors influence your coffee purchasing decision?",
      "category": "product_preferences",
      "response": "Quality is my primary consideration because...",
      "ratings": {
        "authenticity": 4,
        "style_alignment": 4,
        "factual_grounding": 1
      }
    }
  ]
}
```

#### Step 4: Compute Authenticity Metrics

**Metrics:**

1. **Expert Authenticity Score**
   ```
   Average rating across all expert evaluations (1-5 scale)
   ```

2. **Style Alignment Score**
   ```
   Percentage of responses matching expected style profile
   ```
3. **Factual Grounding Score**
   ```
    Percentage of factually accurate responses
   ```