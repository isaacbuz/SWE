#!/usr/bin/env python3
"""
Seed built-in Skills into the database.

This script loads all YAML skill definitions from the skills/ directory
and inserts them into the Skills marketplace database.
"""
import os
import json
import yaml
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/swe_agent"
)

# Remove +asyncpg if present
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")


def load_skill_yaml(file_path: Path) -> Dict[str, Any]:
    """Load a skill YAML file and convert to database format"""
    with open(file_path, 'r') as f:
        skill_data = yaml.safe_load(f)
    
    # Convert to database format
    db_skill = {
        'id': str(uuid4()),
        'name': skill_data['name'],
        'slug': skill_data['slug'],
        'version': skill_data.get('version', '1.0.0'),
        'description': skill_data['description'],
        'detailed_description': skill_data.get('detailed_description'),
        'category': skill_data['category'],
        'tags': skill_data.get('tags', []),
        'prompt_template': skill_data['prompt_template'],
        'input_schema': json.dumps(skill_data['input_schema']),
        'output_schema': json.dumps(skill_data['output_schema']),
        'examples': json.dumps(skill_data.get('examples', [])),
        'model_preferences': json.dumps(skill_data.get('model_preferences', {})),
        'validation_rules': json.dumps(skill_data.get('validation_rules', [])),
        'dependencies': json.dumps(skill_data.get('dependencies', {})),
        'author_name': skill_data.get('author_name', 'AgentOS Team'),
        'author_email': skill_data.get('author_email', 'team@agentos.com'),
        'organization': skill_data.get('organization', 'AgentOS'),
        'visibility': skill_data.get('visibility', 'public'),
        'license': skill_data.get('license', 'MIT'),
        'pricing_model': skill_data.get('pricing_model', 'free'),
        'status': skill_data.get('status', 'active'),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'published_at': datetime.utcnow() if skill_data.get('status') == 'active' else None,
    }
    
    return db_skill


async def seed_skills():
    """Load and insert all skills from YAML files"""
    # Get script directory
    script_dir = Path(__file__).parent
    skills_dir = script_dir / 'skills'
    
    # Find all YAML files
    yaml_files = list(skills_dir.rglob('*.yaml'))
    
    if not yaml_files:
        print("No YAML files found in skills/ directory")
        return
    
    print(f"Found {len(yaml_files)} skill definitions")
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        skills_inserted = 0
        skills_skipped = 0
        
        for yaml_file in yaml_files:
            try:
                # Load skill
                skill = load_skill_yaml(yaml_file)
                
                # Check if skill with same slug already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM skills WHERE slug = $1",
                    skill['slug']
                )
                
                if existing:
                    print(f"  ⏭️  Skipping {skill['slug']} (already exists)")
                    skills_skipped += 1
                    continue
                
                # Insert skill
                await conn.execute(
                    """
                    INSERT INTO skills (
                        id, name, slug, version, description, detailed_description,
                        category, tags, prompt_template, input_schema, output_schema,
                        examples, model_preferences, validation_rules, dependencies,
                        author_name, author_email, organization,
                        visibility, license, pricing_model, status,
                        created_at, updated_at, published_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                        $16, $17, $18, $19, $20, $21, $22, $23, $24, $25
                    )
                    """,
                    skill['id'],
                    skill['name'],
                    skill['slug'],
                    skill['version'],
                    skill['description'],
                    skill['detailed_description'],
                    skill['category'],
                    skill['tags'],
                    skill['prompt_template'],
                    skill['input_schema'],
                    skill['output_schema'],
                    skill['examples'],
                    skill['model_preferences'],
                    skill['validation_rules'],
                    skill['dependencies'],
                    skill['author_name'],
                    skill['author_email'],
                    skill['organization'],
                    skill['visibility'],
                    skill['license'],
                    skill['pricing_model'],
                    skill['status'],
                    skill['created_at'],
                    skill['updated_at'],
                    skill['published_at'],
                )
                
                print(f"  ✅ Inserted {skill['slug']}")
                skills_inserted += 1
                
            except Exception as e:
                print(f"  ❌ Error loading {yaml_file.name}: {e}")
                continue
        
        print(f"\n✅ Successfully inserted {skills_inserted} skills")
        if skills_skipped > 0:
            print(f"⏭️  Skipped {skills_skipped} existing skills")
        
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(seed_skills())

