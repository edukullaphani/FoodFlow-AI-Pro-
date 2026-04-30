# FoodFlow AI Pro

An AI-powered food inventory management system that uses multi-agent reasoning to optimize menu planning, reduce waste, and manage inventory lifecycle.

## Overview

FoodFlow AI Pro is a graph-based pipeline system that processes food inventory data through multiple AI agents to make intelligent decisions about:

- **Inventory Analysis** — Identify at-risk items (near expiry), overstocked items, and safe stock levels
- **Batch Reasoning** — Analyze consumption patterns and trends
- **Decision Making** — Recommend actions (use_now, monitor, safe) for each inventory item
- **Menu Optimization** — Suggest menu items based on available inventory
- **Explanations** — Provide human-readable reasoning for all decisions

## Project Structure

```
foodflow-ai-pro/
├── agents/                    # AI agent implementations
│   ├── batch_reasoning_agent.py
│   ├── decision_agent.py
│   ├── explanation_agent.py
│   └── menu_optimization_agent.py
├── app/
│   ├── main.py               # Entry point for running the pipeline
│   └── dashboard.py          # Optional dashboard UI
├── config/                   # Configuration files
├── core/                     # Core business logic
│   ├── data_processor.py    # CSV data loading & cleaning
│   ├── evaluation.py         # Performance metrics
│   ├── inventory_analysis.py # Stock level analysis
│   └── preprocessing.py      # Signal building
├── data/
│   └── storage.json          # Persistent inventory storage
├── prompts/                  # LLM prompt templates
├── scripts/
│   ├── db.py                 # Database operations
│   └── seed_full_db.py       # Sample data seeding
├── services/
│   └── graph_pipeline.py     # LangGraph pipeline orchestration
├── utils/
│   └── llm_client.py         # LLM integration
└── requirements.txt          # Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

Run the pipeline for multiple days:

```bash
python -m app.main
```

This will:
1. Load sample data from `data/sample.csv`
2. Process inventory through the agent pipeline
3. Display daily decisions, top orders, and explanations
4. Optionally simulate restocking

## Pipeline Architecture

The system uses [LangGraph](https://langchain-ai.github.io/langgraph/) for workflow orchestration:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Data Loading   │────▶│ Inventory Analysis│────▶│ Batch Reasoning │
└─────────────────┘     └──────────────────┘     └──────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Menu Actions  │◀────│    Decisions     │◀────│   Explanation    │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

### Agents

| Agent | Purpose |
|-------|---------|
| `batch_reasoning_agent` | Analyzes consumption patterns and generates insights using LLM |
| `decision_agent` | Rule-based decision making (use_now, monitor, safe) |
| `explanation_agent` | Generates natural language explanations for decisions |
| `menu_optimization_agent` | Suggests optimal menu items based on inventory |

## Configuration

Key settings can be adjusted in the respective agent and core modules:

- **Inventory thresholds** — Define what counts as "at risk" or "overstock"
- **Expiry windows** — Days before expiry to flag items
- **Consumption thresholds** — Rate limits for stock monitoring

## Data Format

Expected CSV format (`data/sample.csv`):

```csv
item_name,category,quantity,unit,expiry_date,price
Tomatoes,vegetables,50,kg,2026-05-01,2.50
Chicken,proteins,30,kg,2026-05-03,8.00
Rice,grains,100,kg,2026-06-15,1.20
```

## Dependencies

- **pandas** — Data processing
- **langgraph** — Pipeline orchestration
- Additional LLM dependencies (see `requirements.txt`)

## License

MIT License