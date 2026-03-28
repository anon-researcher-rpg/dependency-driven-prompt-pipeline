# From World-Gen to Quest-Line: A Dependency-Driven Prompt Pipeline for Coherent RPG Generation

## Overview

This repository contains the implementation of a modular pipeline for procedural content generation (PCG) in role-playing game (RPG) systems using large language models (LLMs).

The project was developed as part of a research study investigating the integration of natural language processing methods into structured game content generation workflows. The system demonstrates how LLMs can be incorporated into deterministic, multi-stage pipelines while preserving reproducibility, structural coherence, and experiment isolation.

The pipeline generates interconnected game artifacts, including:

- World definitions
- Non-player characters (NPCs) and their relationships
- Player character profiles
- Structured missions (quests)
- Expanded narrative arcs
- Graph-based visualizations of character relationships

All outputs are stored as structured JSON artifacts within isolated experiment directories.

---

## System Architecture

The generation process is organized as a sequence of independent but interrelated stages:

1. **World Generation**  
   Produces a structured world model.

2. **NPC Generation**  
   Generates characters embedded in the world and constructs relationship graphs.

3. **Hero Generation**  
   Produces a player character consistent with the world and NPC context.

4. **Mission Generation**  
   Creates structured quests referencing existing world entities.

5. **Mission Expansion**  
   Expands missions into extended narrative arcs.

6. **Visualization**  
   Generates a directed graph of NPC relationships.

Each stage consumes structured JSON outputs from prior stages and produces new artifacts for downstream processing.

---

## Repository Structure

~~~
core/              Configuration, prompts, and utility modules
llm/               OpenAI API client abstraction
stages/            Modular pipeline stages
visualization/     NPC relationship graph generation
pipeline.py        Pipeline orchestration script
requirements.txt   Python dependencies
data/              Generated experiment runs
~~~

Each pipeline execution produces a new run directory:

~~~
data/<MODEL>/<RUN_ID>/
~~~

Example structure:

~~~
data/gpt-5/<RUN_ID>/
├── world/
├── npcs/
├── player/
├── missions/
├── missions_epic/
├── raw/
├── npc_relations_graph.png
└── meta.json
~~~

This design ensures experiment traceability and isolation between runs.

---

## Requirements

- Python 3.10 or higher
- OpenAI API access
- macOS or Linux (tested environments)
- Virtual environment (recommended)

---

## Environment Configuration

Before running the pipeline, define your OpenAI API key as an environment variable.

### macOS / Linux

~~~bash
export OPENAI_API_KEY="your_api_key_here"
~~~

### Windows (PowerShell)

~~~powershell
setx OPENAI_API_KEY "your_api_key_here"
~~~

---

## Installation

Clone the repository, create and activate a virtual environment.

Install dependencies:

~~~bash
pip install -r requirements.txt
~~~

---

## Pipeline Execution

### Full Pipeline Execution

~~~bash
python pipeline.py
~~~

This command:

- Creates a new experiment directory under `data/<MODEL>/<UUID>/`
- Executes all stages sequentially
- Stores structured and raw outputs

---

### Executing Selected Stages

~~~bash
python pipeline.py world npc hero
~~~

---

### Re-running a Stage for an Existing Experiment

~~~bash
python pipeline.py extend_mission \
  --model gpt-5 \
  --run-id <EXISTING_RUN_ID>
~~~

---

### Listing Available Stages

~~~bash
python pipeline.py --list
~~~

---

## Configuration

Primary configuration parameters are defined in:

~~~
core/config.py
~~~

Configurable elements include:

- `MODEL`
- `LANGUAGE`
- Token limits per stage
- Temperature parameters
- Available character classes

Runtime overrides are supported:

~~~bash
python pipeline.py --model gpt-5 --lang EN
~~~

---

## Output Artifacts

Each experiment run produces:

- Structured JSON outputs for all stages
- Raw LLM responses (`raw/`)
- Expanded mission files
- NPC relationship graph visualization
- Run metadata (`meta.json`)

This design supports:

- Controlled experimental comparison across models
- Reproducibility of generated artifacts
- Partial stage re-execution
- Downstream statistical or qualitative analysis

---

## Reproducibility and Experimental Control

Each execution generates a unique run directory:

~~~
data/<MODEL>/<RUN_ID>/
~~~

This guarantees:

- Isolation of experimental results
- Clear model-version traceability
- Deterministic artifact organization
- Structured archival of intermediate outputs
