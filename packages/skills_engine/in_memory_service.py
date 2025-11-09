"""
In-memory Skills service used as a fallback when the database is unavailable.

Loads the built-in YAML skills defined under `packages/skills-library/skills`
and exposes the same interface as `SkillsDatabaseService` for the API router.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL

import yaml

from .models import Skill

logger = logging.getLogger(__name__)

SKILLS_LIBRARY_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "skills-library"
    / "skills"
)


def _now() -> datetime:
    return datetime.utcnow()


def _ensure_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _load_yaml_skills() -> List[Dict[str, Any]]:
    """Load all YAML skill definitions from the skills library."""
    skills: List[Dict[str, Any]] = []

    if not SKILLS_LIBRARY_DIR.exists():
        logger.warning("Skills library directory missing: %s", SKILLS_LIBRARY_DIR)
        return skills

    for yaml_path in SKILLS_LIBRARY_DIR.rglob("*.yaml"):
        try:
            data = yaml.safe_load(yaml_path.read_text())
        except Exception as exc:
            logger.error("Failed to read skill definition %s: %s", yaml_path, exc)
            continue

        if not data or "slug" not in data:
            logger.warning("Skipping invalid skill file %s (missing slug)", yaml_path)
            continue

        skill_id = uuid5(NAMESPACE_URL, f"skill::{data['slug']}")
        timestamp = _now()
        skills.append(
            {
                "id": skill_id,
                "name": data.get("name", data["slug"].replace("-", " ").title()),
                "slug": data["slug"],
                "version": data.get("version", "1.0.0"),
                "description": data.get("description", ""),
                "detailed_description": data.get("detailed_description"),
                "category": data.get("category", "GENERAL"),
                "tags": data.get("tags", []),
                "prompt_template": data.get("prompt_template", ""),
                "input_schema": data.get("input_schema", {}),
                "output_schema": data.get("output_schema", {}),
                "examples": data.get("examples"),
                "model_preferences": data.get("model_preferences", {}),
                "validation_rules": data.get("validation_rules"),
                "visibility": data.get("visibility", "public"),
                "license": data.get("license", "MIT"),
                "pricing_model": data.get("pricing_model", "free"),
                "status": data.get("status", "active"),
                "author_id": None,
                "author_name": data.get("author_name"),
                "author_email": data.get("author_email"),
                "organization": data.get("organization"),
                "download_count": 0,
                "installation_count": 0,
                "execution_count": 0,
                "avg_rating": 0.0,
                "review_count": 0,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )

    return skills


@dataclass
class _Installation:
    id: UUID
    skill_id: UUID
    user_id: UUID
    version: str
    auto_update: bool
    enabled: bool = True
    installed_at: datetime = field(default_factory=_now)
    last_used_at: Optional[datetime] = None
    use_count: int = 0


class InMemorySkillsService:
    """
    Lightweight Skills service that mirrors the async API of `SkillsDatabaseService`.
    """

    def __init__(self):
        self._skills: Dict[UUID, Dict[str, Any]] = {
            skill["id"]: skill for skill in _load_yaml_skills()
        }
        self._skills_by_slug: Dict[str, Dict[str, Any]] = {
            skill["slug"]: skill for skill in self._skills.values()
        }
        self._installations: Dict[UUID, Dict[UUID, _Installation]] = {}
        self._executions: Dict[UUID, Dict[str, Any]] = {}
        self._reviews: Dict[UUID, List[Dict[str, Any]]] = {}
        logger.info(
            "Initialized in-memory skills service with %d skills",
            len(self._skills),
        )

    async def list_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        visibility: Optional[str] = None,
        status: str = "active",
        sort: str = "updated_at",
        order: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        skills = list(self._skills.values())

        if status:
            skills = [s for s in skills if s.get("status") == status]
        if category:
            skills = [s for s in skills if s.get("category") == category]
        if visibility:
            skills = [s for s in skills if s.get("visibility") == visibility]
        if tags:
            tag_set = set(tags)
            skills = [
                s for s in skills if tag_set.intersection(set(s.get("tags", [])))
            ]
        if search:
            term = search.lower()
            skills = [
                s
                for s in skills
                if term in s.get("name", "").lower()
                or term in s.get("description", "").lower()
            ]

        reverse = order.lower() != "asc"
        skills.sort(key=lambda s: s.get(sort) or s.get("updated_at"), reverse=reverse)

        return skills[offset : offset + limit]

    async def get_skill_by_id(self, skill_id: UUID) -> Optional[Dict[str, Any]]:
        skill_id = _ensure_uuid(skill_id)
        return self._skills.get(skill_id)

    async def get_skill_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        return self._skills_by_slug.get(slug)

    async def create_skill(
        self,
        skill_data: Dict[str, Any],
        author_id: UUID,
    ) -> Dict[str, Any]:
        skill_id = uuid4()
        timestamp = _now()
        new_skill = {
            **skill_data,
            "id": skill_id,
            "author_id": author_id,
            "version": skill_data.get("version", "1.0.0"),
            "download_count": 0,
            "installation_count": 0,
            "execution_count": 0,
            "avg_rating": 0.0,
            "review_count": 0,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._skills[skill_id] = new_skill
        self._skills_by_slug[new_skill["slug"]] = new_skill
        return new_skill

    async def update_skill(
        self,
        skill_id: UUID,
        updates: Dict[str, Any],
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        skill_id = _ensure_uuid(skill_id)
        user_id = _ensure_uuid(user_id)
        skill = self._skills.get(skill_id)

        if not skill:
            return None

        owner = skill.get("author_id")
        if owner is None:
            raise PermissionError("Managed skills cannot be updated")
        if owner != user_id:
            raise PermissionError("Only the skill owner can update this skill")

        allowed_fields = {
            "name",
            "description",
            "detailed_description",
            "category",
            "tags",
            "prompt_template",
            "input_schema",
            "output_schema",
            "examples",
            "model_preferences",
            "validation_rules",
            "status",
        }

        changed = False
        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                skill[key] = value
                changed = True

        if changed:
            skill["updated_at"] = _now()

        return skill

    async def log_execution(self, execution_data: Dict[str, Any]) -> UUID:
        execution_id = uuid4()
        execution_data = {
            **execution_data,
            "id": execution_id,
            "executed_at": execution_data.get("executed_at", _now()),
        }
        self._executions[execution_id] = execution_data

        skill = self._skills.get(_ensure_uuid(execution_data["skill_id"]))
        if skill:
            skill["execution_count"] = skill.get("execution_count", 0) + 1
            skill["updated_at"] = _now()

        user_id = execution_data.get("user_id")
        if user_id:
            user_id = _ensure_uuid(user_id)
            installations = self._installations.get(user_id, {})
            install = installations.get(_ensure_uuid(execution_data["skill_id"]))
            if install:
                install.use_count += 1
                install.last_used_at = _now()

        return execution_id

    async def install_skill(
        self,
        skill_id: UUID,
        user_id: UUID,
        version: Optional[str] = None,
        auto_update: bool = True,
    ) -> Dict[str, Any]:
        skill_id = _ensure_uuid(skill_id)
        user_id = _ensure_uuid(user_id)
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError("Skill not found")

        if not version:
            version = skill.get("version", "1.0.0")

        user_installs = self._installations.setdefault(user_id, {})
        installation = user_installs.get(skill_id)
        if installation:
            installation.version = version
            installation.auto_update = auto_update
            installation.enabled = True
        else:
            installation = _Installation(
                id=uuid4(),
                skill_id=skill_id,
                user_id=user_id,
                version=version,
                auto_update=auto_update,
            )
            user_installs[skill_id] = installation
            skill["installation_count"] = skill.get("installation_count", 0) + 1

        return installation.__dict__

    async def uninstall_skill(self, skill_id: UUID, user_id: UUID) -> bool:
        skill_id = _ensure_uuid(skill_id)
        user_id = _ensure_uuid(user_id)
        installs = self._installations.get(user_id, {})
        if skill_id in installs:
            del installs[skill_id]
            return True
        return False

    async def list_installed_skills(self, user_id: UUID) -> List[Dict[str, Any]]:
        user_id = _ensure_uuid(user_id)
        installs = self._installations.get(user_id, {})
        return [inst.__dict__ for inst in installs.values()]

    async def list_skill_reviews(
        self,
        skill_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        skill_id = _ensure_uuid(skill_id)
        reviews = self._reviews.get(skill_id, [])
        return reviews[offset : offset + limit]

    async def create_skill_review(
        self,
        skill_id: UUID,
        user_id: UUID,
        rating: int,
        title: Optional[str],
        review_text: Optional[str],
    ) -> Dict[str, Any]:
        skill_id = _ensure_uuid(skill_id)
        user_id = _ensure_uuid(user_id)
        if skill_id not in self._skills:
            raise ValueError("Skill not found")

        review = {
            "id": uuid4(),
            "skill_id": skill_id,
            "user_id": user_id,
            "rating": rating,
            "title": title,
            "review_text": review_text,
            "created_at": _now(),
        }

        self._reviews.setdefault(skill_id, []).append(review)

        skill = self._skills[skill_id]
        reviews = self._reviews[skill_id]
        total_rating = sum(r["rating"] for r in reviews)
        skill["review_count"] = len(reviews)
        skill["avg_rating"] = round(total_rating / len(reviews), 2)
        skill["updated_at"] = _now()

        return review

    async def list_skill_versions(
        self,
        skill_id: UUID,
    ) -> List[Dict[str, Any]]:
        """List versions for a skill (in-memory implementation returns current version)."""
        skill_id = _ensure_uuid(skill_id)
        skill = self._skills.get(skill_id)
        if not skill:
            return []
        
        # Return current version as a version entry
        return [{
            "id": uuid4(),
            "skill_id": skill_id,
            "version": skill.get("version", "1.0.0"),
            "changelog": None,
            "breaking_changes": False,
            "migration_guide": None,
            "status": "active",
            "created_at": skill.get("created_at", _now()),
        }]

    async def get_skill_analytics(
        self,
        skill_id: UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        skill_id = _ensure_uuid(skill_id)
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError("Skill not found")

        reviews = self._reviews.get(skill_id, [])
        rating_breakdown: Dict[int, int] = {star: 0 for star in range(1, 6)}
        for review in reviews:
            rating_breakdown[review["rating"]] += 1

        return {
            "skill_id": str(skill_id),
            "start_date": start_date,
            "end_date": end_date,
            "executions": skill.get("execution_count", 0),
            "installations": skill.get("installation_count", 0),
            "downloads": skill.get("download_count", 0),
            "avg_rating": skill.get("avg_rating", 0),
            "review_count": skill.get("review_count", 0),
            "rating_breakdown": rating_breakdown,
            "updated_at": _now().isoformat(),
        }

    def skill_dict_to_model(self, skill_dict: Dict[str, Any]) -> Skill:
        return Skill(
            id=str(skill_dict["id"]),
            name=skill_dict["name"],
            slug=skill_dict["slug"],
            version=skill_dict["version"],
            description=skill_dict["description"],
            prompt_template=skill_dict["prompt_template"],
            input_schema=json.loads(json.dumps(skill_dict["input_schema"])),
            output_schema=json.loads(json.dumps(skill_dict["output_schema"])),
            model_preferences=skill_dict.get("model_preferences", {}),
            validation_rules=skill_dict.get("validation_rules"),
            category=skill_dict.get("category", "GENERAL"),
            created_at=skill_dict.get("created_at"),
            updated_at=skill_dict.get("updated_at"),
        )


_in_memory_service: Optional[InMemorySkillsService] = None
_service_lock = asyncio.Lock()


async def get_in_memory_skills_service() -> InMemorySkillsService:
    """
    Return a singleton instance of the in-memory skills service.
    """
    global _in_memory_service

    if _in_memory_service is None:
        async with _service_lock:
            if _in_memory_service is None:
                _in_memory_service = InMemorySkillsService()

    return _in_memory_service
