# MetricMind - Project Plan

## 1. Project Overview

MetricMind is an AI-powered Agentic Business Intelligence platform that allows users to ask business questions in natural language.

Instead of allowing an LLM to generate raw SQL directly against the database, MetricMind uses a governed Semantic Layer containing officially defined business metrics and dimensions. The AI Agent understands the user's question, retrieves the required governed data, performs analysis, and presents a reliable answer with relevant visualizations.

---

## 2. Problem Statement

Traditional Text-to-SQL systems can produce incorrect queries, hallucinate table joins, ignore business logic, and generate inconsistent business metrics.

MetricMind aims to solve this problem by ensuring that the AI Agent works only with approved metric definitions from a Semantic Layer.

For example, when a user asks:

> Why did European margins drop last quarter?

The AI Agent will:

1. Identify the required metric and filters.
2. Request governed data from the Semantic Layer.
3. Compare the relevant time periods.
4. Perform additional breakdown analysis if required.
5. Generate an explanation based only on the returned data.

---

## 3. Project Objectives

The main objectives of MetricMind are to:

- Build a conversational Business Intelligence application.
- Allow users to ask business questions in natural language.
- Use a Semantic Layer to maintain consistent metric definitions.
- Prevent uncontrolled Text-to-SQL and SQL hallucinations.
- Build an AI Agent capable of multi-step analysis.
- Automatically investigate possible reasons behind important metric changes.
- Display relevant charts along with AI-generated insights.
- Provide transparent and reliable business analysis.

---

## 4. Core Features

### 4.1 Natural Language Business Queries

Users can ask questions such as:

- What was our revenue last quarter?
- Show revenue by region.
- Which product category is the most profitable?
- Compare this quarter with the previous quarter.
- Why did European margins drop?

### 4.2 Governed Semantic Metrics

The system will use approved definitions for business metrics such as:

- Revenue
- Cost
- Profit
- Profit Margin
- Order Count
- Average Order Value

Dimensions may include:

- Time
- Region
- Country
- Product
- Product Category

### 4.3 AI Agent

The AI Agent will:

- Understand the user's question.
- Identify the required metrics and filters.
- Access only approved metrics and dimensions.
- Call the Semantic Layer instead of generating raw SQL.
- Analyze the returned data.
- Perform additional analysis for "why" or root-cause questions.
- Generate a clear final explanation.

### 4.4 Multi-Step Root-Cause Analysis

For questions such as:

> Why did profit decrease?

The agent will perform multiple analytical steps, such as:

1. Check the profit trend.
2. Compare the current and previous periods.
3. Analyze revenue and cost changes.
4. Break down the results by region or category.
5. Identify the major contributors to the change.
6. Generate an evidence-based explanation.

### 4.5 Conversational BI Interface

The application will provide:

- Chat-based interaction.
- AI-generated answers.
- Dynamic charts.
- Metric and filter information.
- Follow-up questions using conversation context.

---

## 5. Project Architecture

User
  ↓
Frontend - Conversational BI Interface
  ↓
FastAPI Backend
  ↓
AI Agent
  ↓
Semantic Layer
  ↓
Database
  ↓
Returned Data
  ↓
AI Analysis + Charts
  ↓
User

---

## 6. Technology Stack

### Frontend

- React or Next.js
- TypeScript/JavaScript
- ECharts for data visualization

### Backend

- Python
- FastAPI
- Pydantic

### AI Agent

- Python
- LangChain
- LLM
- Structured output and tool calling

### Data and Semantic Layer

- PostgreSQL
- Cube.dev
- SQL
- Pandas

### Testing and Validation

- Python
- pytest
- Pandas
- SQL

### Version Control

- Git
- GitHub

### Optional Deployment

- Docker
- Docker Compose

---

## 7. Team Roles

### 1. AI Agent Engineer and Team Lead

Responsibilities:

- Build the AI Agent.
- Implement LLM integration.
- Develop query understanding and structured outputs.
- Build tools for Semantic Layer interaction.
- Implement multi-step and root-cause analysis.
- Coordinate the team and manage project progress.

### 2. Data and Semantic Engineer

Responsibilities:

- Select and understand the dataset.
- Clean and transform the data.
- Design the database structure.
- Load data into PostgreSQL.
- Define business metrics and dimensions.
- Configure the Semantic Layer.

### 3. Backend and API Engineer

Responsibilities:

- Build the FastAPI backend.
- Create APIs for chat and data interaction.
- Connect the frontend, AI Agent, Semantic Layer, and database.
- Handle validation and error handling.
- Support system integration.

### 4. Frontend and Data Visualization Engineer

Responsibilities:

- Build the application interface.
- Create the chat experience.
- Integrate frontend APIs.
- Display AI responses.
- Build dynamic and interactive charts.
- Improve the user experience.

### 5. Analytics and AI Validation Engineer

Responsibilities:

- Perform exploratory data analysis.
- Validate business metrics.
- Create meaningful business questions and test cases.
- Verify that AI answers are supported by actual data.
- Test invalid, ambiguous, and unavailable queries.
- Check consistency and hallucination prevention.

---

## 8. Innovative Features

The following features will be added to make MetricMind more advanced:

### 8.1 Evidence and Confidence Panel

Each AI answer can show:

- Metric used.
- Filters applied.
- Dimensions used.
- Data source details.
- Analysis steps performed.

### 8.2 Proactive Insights

MetricMind will identify important changes automatically.

Example:

> European revenue dropped significantly compared with the previous period. Would you like me to investigate why?

### 8.3 Automatic Investigation

When an important anomaly or significant change is detected, the system can automatically perform breakdown analysis to identify possible contributors.

### 8.4 Smart Chart Recommendation

Based on the returned data, the system can automatically select an appropriate visualization such as:

- Line chart for trends.
- Bar chart for comparisons.
- Pie or donut chart for distributions.

### 8.5 Conversational Follow-Up Analysis

Users can ask follow-up questions such as:

- Why?
- Show it by country.
- Compare it with last quarter.
- Which category contributed the most?

The system should use conversation context where appropriate.

---

## 9. Development Phases

### Phase 1 - Project Foundation

- Finalize architecture.
- Assign team roles.
- Select the dataset.
- Set up the repository and branches.
- Create the frontend and backend foundations.
- Set up the database.
- Begin data exploration.

### Phase 2 - Core Semantic and Application Development

- Clean and transform the dataset.
- Define metrics and dimensions.
- Configure the Semantic Layer.
- Build the chat interface.
- Build the FastAPI APIs.
- Connect the core application components.

### Phase 3 - AI Agent Development

- Implement natural language query understanding.
- Add metric and dimension validation.
- Connect the AI Agent to the Semantic Layer.
- Implement basic question answering.
- Test correct API/query generation.

### Phase 4 - Advanced Analytics

- Add multi-step reasoning.
- Implement root-cause analysis.
- Add dynamic chart selection.
- Add conversational follow-up questions.
- Implement proactive insights.

### Phase 5 - Testing and Finalization

- Validate metric consistency.
- Test AI responses against actual data.
- Test edge cases and invalid queries.
- Perform end-to-end integration testing.
- Improve the UI and user experience.
- Prepare documentation and final presentation.

---

## 10. Success Criteria

MetricMind will be considered successful when:

- Users can ask business questions in natural language.
- The AI uses approved metrics from the Semantic Layer.
- The system avoids uncontrolled raw SQL generation.
- The same governed query produces consistent results.
- The AI correctly applies requested filters and dimensions.
- Root-cause questions trigger additional analysis.
- AI explanations are supported by returned data.
- Relevant charts are displayed.
- The complete system works end-to-end.

---

## 11. Expected Final Outcome

The final MetricMind application will function as an intelligent business analytics assistant.

It will combine:

Natural Language
+
AI Agent
+
Governed Business Metrics
+
Semantic Layer
+
Reliable Data
+
Automated Analysis
+
Interactive Visualizations

The goal is to create a system that is more reliable than a normal Text-to-SQL chatbot and more interactive than a traditional static dashboard.

## Technology Stack & Team Roles

The MetricMind project will use the following technologies according to each team member's role:

# Data & Semantic Engineer
Snowflake, dbt, Cube.dev, and YAML will be used for data storage, transformation, and defining governed business metrics and dimensions.

# AI Agent Engineer
Python, LangChain, Llama 3, and the Cube.dev API will be used to build the AI agent that converts natural language questions into semantic API queries.

# Backend & Integration Engineer
Python, REST APIs, JSON, and Cube.dev API integration will be used to connect the different components of the system.

# Frontend & Visualization Engineer
Next.js, Tremor, and ECharts will be used to build the conversational BI interface and interactive data visualizations.

# Analytics & Insight Engineer
Python and Pandas will be used for data analysis, KPI calculation, trend analysis, anomaly detection, proactive insights, and AI result validation.