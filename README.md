# Rule-Based Computer Troubleshooting Expert System

A web-based expert system that diagnoses common computer problems using **forward chaining**, certainty factors, dynamic questioning, and an explanation layer.

## Overview

Instead of returning a black-box prediction, the system keeps an explicit working memory of facts, fires interpretable IF–THEN rules, asks follow-up questions when evidence is missing, and explains how a diagnosis was reached.

### Knowledge base

| Component | Current size |
| --- | ---: |
| Questions | 50 |
| IF–THEN rules | 103 |
| Diagnoses | 50 |
| Symptom facts | ~166 |
| Diagnostic groups | 8 |

The knowledge base covers power/boot, display, Windows/OS, networking, audio/camera, peripherals, performance/thermal issues, and storage.

## Inference pipeline

```text
User message
   |
   v
NLU / fact extraction
   |
   v
Working memory
   |
   v
MATCH applicable rules
   |
   v
SELECT by priority / specificity / certainty
   |
   v
FIRE rule
   |
   +--> add facts
   +--> trigger diagnosis
   +--> request missing evidence
   |
   v
Explanation builder
```

## Key ideas

### Forward chaining

The inference engine repeatedly matches rules against known facts and fires applicable rules until no further useful rule can be activated.

### Certainty factor

When multiple rules support the same diagnosis, confidence can be combined using the MYCIN-style formulation:

```text
CFcombined = CF1 + CF2 * (1 - CF1)
```

### Dynamic questioning

The next question is selected from missing evidence instead of following one fixed questionnaire. The scoring logic considers coverage, discrimination between candidate diagnoses, group relevance, and rule proximity.

### Explainability

The system keeps enough inference state to show the evidence and reasoning path behind a result.

## Architecture

```text
Browser chat UI
      |
      v
Flask application
      |
      +---- NLU / fact extraction
      |
      +---- inference engine
      |       ├── working memory
      |       ├── rule model
      |       ├── forward chaining
      |       ├── question selector
      |       └── explanation builder
      |
      +---- session service
      |
      v
JSON knowledge base
```

## Tech stack

- Python
- Flask
- HTML / CSS / JavaScript
- JSON knowledge base
- pytest

## Repository structure

```text
engine/          inference engine
nlu/             intent and fact extraction
services/        session services
knowledge_base/  source knowledge base
data/            runtime knowledge-base data
templates/       Flask templates
static/          browser UI assets
tests/           unit and integration tests
docs / reports   academic and technical documentation
```

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://localhost:5000
```

## Tests

```bash
python -m pytest tests/ -v
```

The repository contains engine, NLU, and application-flow tests.

## Optional messaging integrations

The project also contains experimental Meta webhook flows for Messenger / Instagram demos. Credentials are supplied only through environment variables; real access tokens should never be committed to the repository.

## Team

Developed as an academic Knowledge Technology project at Saigon University by:

- Do Duy Quy
- Lu Hong Phuc
- Nguyen Huu Tri
- Nguyen Dang Khoa

## Why this project matters

The goal is not just to classify a symptom, but to demonstrate a transparent symbolic-AI workflow: explicit facts, explicit rules, controlled conflict resolution, uncertainty handling, interactive evidence collection, and human-readable explanations.
