# System design

## Overview

The Lavazza AI Personas project is a comprehensive technical initiative undertaken in collaboration with Politecnico di Torino, aiming to transform static consumer segmentation studies into dynamic, conversational AI agents.

## Requirements

The Lavazza AI Personas project is a comprehensive technical initiative aimed at creating dynamic, conversational AI agents that authentically represent Lavazza's customer segments.

The project requires the development of a bespoke system that balances authentic personality with factual accuracy and transparency, intentionally moving away from the common biases found in large commercial models.

### I. Project Goal (Objective)

The overarching goal is to transform **static customer segmentation studies** into **dynamic, conversational AI agents**. These personas will serve as a next-generation consumer insights platform and a dynamic tool for market research, idea validation, and strategic decision-making within Lavazza.

Key strategic and ultimate goals include:

*   **Accelerating Insights:** Providing marketing teams and researchers with a sparring partner to validate concepts, test campaigns, and gather consumer insights in real-time.
*   **Trust and Transparency:** Building the solution **from scratch** to gain greater transparency over the models' logic and reduce the inherent bias found in pre-trained large commercial models (like ChatGPT), which often rely too heavily on generic information rather than proprietary Lavazza data.
*   **Ultimate Deliverable:** Creating a **user-friendly chat frontend** through which internal teams can interact with the synthetic personas.

### II. Key Project Requirements

The requirements are divided into functional (what the personas must achieve) and architectural/data (how the system must be built).

#### A. Persona Behavior and Functional Requirements

The project mandates specific, sophisticated behavioral requirements to ensure the personas are reliable and useful for critical business decisions:

| Requirement Category | Specific Mandates                                                                                                                                                                                                                                               |
| :--- |:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Factual Accuracy** | The algorithm must find and provide **precise, detailed answers** that are explicitly written within the source documentation.                                                                                                                                  | 
| **Non-Hallucination (Crucial)** | The personas must avoid fabrications or "hallucinations". If the persona lacks sufficient data on a topic, it is explicitly preferred that they answer: **"I don't have enough data on this topic"**.                                                           |
| **Authenticity and Tone** | Responses must be **coherent and consistent** with the specific segment description. The language should reflect the persona's defined style, based on real customer quotes and narratives stored in their profile.                                             |
| **Critical Thinking** | The persona must be capable of providing **critical, negative feedback** or refusing ideas if they conflict with its profile, rather than simply trying to please the audience. This requires a deliberate engineering effort.                                  |
| **Transparency (Explainability)** | The solution must allow the user to understand the LLM’s logic. It must have a **connection to the source** of the information, clearly indicating if the answer came from Lavazza's internal documentation or from generic external sources.                   |
| **Multimodal Input** | The chat interface must support processing **text, visuals, and PDF documents** (e.g., packaging designs, concept notes).                                                                                                                                       |
| **Virtual Focus Groups** | The system must be able to simulate a **virtual focus group** by allowing users to interact with and receive simultaneous, separate feedback from multiple AI personas.                                                                                         |

#### B. Data and Foundation Requirements

The personas must be built on a reliable, proprietary data foundation:

1.  **Proprietary Segmentation Studies:** The primary source of qualitative insight is Lavazza's **Customer Segmentation Studies** (in PDF format), detailing nuanced descriptions and motivations of customer segments.
2.  **Quantitative Market Data:** The system must integrate tabular data, providing the quantitative backbone, including demographic profiles and behavioral patterns like purchase frequency and product preferences.
3.  **Data Extraction Challenge:** Significant effort is required to extract information from the PDF documentation, which includes numerous images and plots, to make it machine-readable for the LLM.
4.  **Unified Schema:** Data from heterogeneous sources must be synthesized into a **Unified Persona Profile Schema** (a JSON object) covering demographics, psychographics, behavioral data, and narrative/verbatim excerpts.

#### C. Technical and Enterprise Requirements

1.  **Architecture:** The recommended architecture is a **Hybrid RAG-Tuning Model** that uses:
    *   **Retrieval-Augmented Generation (RAG):** To provide factual grounding from the knowledge base, drastically reducing hallucination and enabling traceability.
    *   **Parameter-Efficient Fine-Tuning (PEFT), such as LoRA:** To instill the required personality, critical thinking style, and nuanced voice into the model.
2.  **Model Choice:** The system should utilize a state-of-the-art **open-source LLM** (e.g., Llama 3 or Mistral families) to ensure full control, prevent vendor lock-in, and maintain data security and privacy through local or private cloud deployment.

## Project Structure

Implementation work follows the Cookiecutter Data Science layout already summarized in `README.md`, which keeps experimentation assets, production code, and documentation isolated yet connected. Highlights:

- **`adsp/`** – Houses the full implementation stack. Each module aligns with a layer from the architecture:
  - `app/` – persona configuration, ingestion, reporting, Q&A, and auth services.
  - `fe/` – frontend prototypes that connect authentication with the chat UI.
  - `communication/` – RPC, cache, and event broker abstractions.
  - `core/` – modular packages for the orchestrator, input processing, prompt construction, retrieval, persona routing, memory, and MCP-powered tool access.
  - `data_pipeline/` – document ingestion, schema enforcement, transformations, and vector-store builders.
  - `modeling/` – PEFT training utilities plus runtime inference adapters.
  - `monitoring/` – evaluation harnesses and metrics collection.
  - `storage/` / `utils/` – business DB, object storage, vector DB clients, logging, and exceptions.
- **`data/`** – Canonical storage for raw, interim, processed, and external datasets. It mirrors the ingestion and RAG pipelines by enforcing immutability of `raw/` inputs and reproducibility of downstream artifacts.
- **`docs/`** – Architectural material, including this design blueprint and `docs/folder_structure.md`, which keeps the README-aligned breakdown of every folder so engineers can quickly locate assets tied to each system capability.
- **`models/`, `reports/`, and `notebooks/`** – Hold serialized persona checkpoints, generated analysis, and exploratory research notebooks, respectively, ensuring model development and monitoring assets remain auditable.

Refer to `docs/folder_structure.md` whenever you need the full tree, naming conventions, or ownership expectations for a given path.

## System Architecture

### System Architecture Overview

![](../images/ai%20persona%20-%20System%20Architecture%20Overview.png)

#### **1. User Interface (UI)**

The user interface serves as the system’s entry point, built as a **Frontend (FE)** application. It enables users to interact seamlessly with the platform, submit queries, upload data, and view results or reports.

#### **2. Application Layer**

This layer contains the core application logic and manages all user-driven workflows.

Key components include:

- **Persona Configuration:** Enables users to select or customize AI personas dynamically.
- **Ingestion Service:** Handles ingestion of raw data such as PDFs or images and stores them in **S3**.
- **Report Service:** Generates structured, formatted reports from processed and analyzed data.
- **Q&A Service:** Manages interactive question-and-answer exchanges with the AI.
- **Auth Service:** Provides authentication and authorization for users, ensuring secure access and operations.


#### **3. Communication Layer**

This layer facilitates efficient communication and coordination among microservices.

- **RPC Server:** Enables direct service-to-service communication via Remote Procedure Calls.
- **Cache:** A high-speed memory layer that stores frequently accessed data to optimize performance.
- **Event Broker / Message Queue (RabbitMQ or Kafka):** Handles asynchronous communication and event-driven processing across services, ensuring reliability, scalability, and robust monitoring.


#### **4. Core Layer**

The intelligence engine of the system—handles AI persona logic, LLM orchestration, and data-driven grounding.

- **Orchestrator:** The central coordinator of the Core Layer. When a request arrives, the Orchestrator manages the entire generation process, directing which services to call.
- **Input Handler:** Preprocesses and normalizes user inputs, including text extraction from PDFs and preparation of image data for AI analysis.
- **Prompt Construction:** Dynamically builds structured prompts by combining user input, persona rules, and retrieved data.
- **AI Persona Router:** Selects fine-tuned Large Language Models (LLMs) tailored to embody distinct customer segment personalities, generating output accordingly.
- **RAG (Retrieval-Augmented Generation):** Provides factual grounding by retrieving relevant information from the **Vector DB**, ensuring responses remain accurate.
- **Persona Registry:** Stores the static attributes and behavioral definitions of each persona, guiding prompt construction and response tone.
- **Explanation:** This module allows for an in-depth explanation of the thought process behind the reasoning model and the data used in the thinking process.
- **MCP Server (Model Context Protocol Server):** Enriches LLM interactions with real-time contextual or external domain data.
- **Memory:** It stores the recent history of the user's chat, allowing the persona to remember what was said earlier in the conversation and provide context-aware answers.


#### **5. Monitoring and Evaluation**

A centralized observability layer that tracks performance, quality, and reliability across all services.

- **Evaluation Tools:** Measure the accuracy and quality of AI responses and data processing outcomes.
- **Metrics & Alerting:** Monitor key indicators such as latency, error rates, resource utilization, and token usage, triggering alerts for anomalies or system degradation.


#### **6. Data Storage Layer**

The persistence foundation of the system, designed for scalability, durability, and speed.

- **Business Logic Database:** Stores structured data such as user profiles, authentication records, saved reports, and persona definitions.
- **Object Storage (S3):** Manages large, unstructured data files (e.g., raw PDFs, images, and uploaded datasets).
- **Vector Database:** Stores embeddings for persona-related documents, historical interactions, and reference materials — powering RAG retrieval and factual grounding.

### Functional Diagram

#### 1. Process Flow Overview

![](../images/ai%20persona-Functional%20diagram%20overview.png)

##### 1. User Query Submission
- User sends a query with optional attached files (image, PDF, etc.) to the **Orchestrator**.

###### 1.1 Orchestrator Analysis
- The Orchestrator analyzes the query and attachments to decide which services should be used.

##### 2. Input Preprocessing
- Inputs are preprocessed before passing to the model.

###### 2.1 Text Input
- Normalize text to make it easier to handle in later steps.

###### 2.2 PDF Input
- Parse, process, and extract meaningful information from PDF files.

###### 2.3 Image Input
- Process images and extract valuable information.

##### 3. Context Retrieval (RAG System)
- Use the query and relevant input information to retrieve context (e.g., market data) via a **RAG system**.

##### 4. Tool Selection & MCP Server Requests
- Decide which tools should be used to enrich the context.
- Send requests to the **MCP server** to gather corresponding context.

###### 4.1 Web Search
- Extract updated information from the internet (trends, real-time data, missing internal data, etc.).

###### 4.2 Database Query
- Retrieve useful data from internal or external databases.

###### 4.3 External APIs
- Call APIs to obtain additional information.

###### 4.4 Other Tools
- Use calculators, simulators, weather data extractors, or other utilities to enrich context.

##### 5. Explanation
- The explanation module will explain in detail the thought process of the reasoning model and the data used for the thinking process.

##### 6. Prompt Construction
- The Orchestrator aggregates useful context and passes it to **Prompt Construction**.

##### 7. Persona Selection
- Apply the selected Persona profile, including:
  - Demographics  
  - Behavior Data  
  - Transactional Data

##### 8. Memory Integration
- Extract useful information from **chat history**.

##### 9. Persona Model Routing
- Route to a fine-tuned Persona model.
- Pass the enriched prompt and context.

##### 10. Model Response
- Generate a response with:
  - Specific personality  
  - Tone  
  - Linguistic style of the Persona

#### 2. Background Processing - PEFT AI Personas

![](../images/ai%20persona%20-Functional%20diagram%20peft.png)

#### 3. Background Processing - Rag Indexing

![](../images/ai%20persona%20-%20Functional%20diagram%20rag.png)
