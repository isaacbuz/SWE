# Built-in Skills Library

A collection of 15+ production-ready Skills for common software engineering tasks.

## Overview

This library contains pre-built Skills that can be installed and used immediately. Skills are defined in YAML format and can be loaded into the Skills marketplace database.

## Categories

- **Code Generation** (4 Skills)
- **Testing** (3 Skills)
- **Code Review** (3 Skills)
- **Documentation** (3 Skills)
- **Architecture** (3 Skills)

## Usage

Skills can be loaded into the database using the seed script:

```bash
python packages/skills-library/seed_skills.py
```

Or via the API:

```bash
curl -X POST http://localhost:8000/api/v1/skills \
  -H "Content-Type: application/json" \
  -d @packages/skills-library/skills/code-generation/typescript-api-endpoint.yaml
```

## Skills List

See individual YAML files in the `skills/` directory for complete definitions.
