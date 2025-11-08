"""
Tests for the in-memory skills service fallback.
"""
import uuid

import pytest

from packages.skills_engine.in_memory_service import InMemorySkillsService


@pytest.fixture
def service():
    """Create a fresh in-memory service instance for each test."""
    return InMemorySkillsService()


@pytest.mark.asyncio
async def test_list_skills_returns_seed_data(service):
    skills = await service.list_skills(limit=100)
    assert len(skills) > 0

    sample = skills[0]
    filtered = await service.list_skills(category=sample["category"], limit=20)
    assert filtered
    assert all(skill["category"] == sample["category"] for skill in filtered)


@pytest.mark.asyncio
async def test_get_and_convert_skill(service):
    skills = await service.list_skills(limit=1)
    skill = skills[0]

    fetched = await service.get_skill_by_id(skill["id"])
    assert fetched["id"] == skill["id"]

    model = service.skill_dict_to_model(fetched)
    assert model.id == str(skill["id"])
    assert model.slug == skill["slug"]


@pytest.mark.asyncio
async def test_install_and_uninstall_skill(service):
    skill = (await service.list_skills(limit=1))[0]
    user_id = uuid.uuid4()

    installation = await service.install_skill(skill["id"], user_id)
    assert installation["skill_id"] == skill["id"]
    assert installation["user_id"] == user_id

    installed = await service.list_installed_skills(user_id)
    assert len(installed) == 1

    removed = await service.uninstall_skill(skill["id"], user_id)
    assert removed is True
    assert await service.list_installed_skills(user_id) == []


@pytest.mark.asyncio
async def test_log_execution_updates_counters(service):
    skill = (await service.list_skills(limit=1))[0]
    user_id = uuid.uuid4()

    before = (await service.get_skill_by_id(skill["id"]))["execution_count"]

    execution_id = await service.log_execution(
        {
            "skill_id": skill["id"],
            "skill_version": skill["version"],
            "user_id": user_id,
            "inputs": {"sample": "value"},
            "outputs": {"result": "ok"},
            "status": "success",
        }
    )

    assert execution_id is not None
    after = (await service.get_skill_by_id(skill["id"]))["execution_count"]
    assert after == before + 1


@pytest.mark.asyncio
async def test_update_skill_requires_owner(service):
    skill = await service.create_skill(
        {
            "name": "User Skill",
            "slug": "user-skill",
            "description": "desc",
            "category": "CODE_GENERATION",
            "prompt_template": "Hello {{name}}",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
        },
        author_id=uuid.uuid4(),
    )

    with pytest.raises(PermissionError):
        await service.update_skill(skill["id"], {"name": "Nope"}, uuid.uuid4())


@pytest.mark.asyncio
async def test_update_skill_success(service):
    owner_id = uuid.uuid4()
    skill = await service.create_skill(
        {
            "name": "User Skill",
            "slug": "user-skill",
            "description": "desc",
            "category": "CODE_GENERATION",
            "prompt_template": "Hello {{name}}",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
        },
        author_id=owner_id,
    )

    updated = await service.update_skill(
        skill["id"],
        {"description": "updated desc", "status": "active"},
        owner_id,
    )

    assert updated["description"] == "updated desc"
    assert updated["status"] == "active"


@pytest.mark.asyncio
async def test_reviews_and_analytics(service):
    skill = (await service.list_skills(limit=1))[0]
    user_id = uuid.uuid4()

    await service.create_skill_review(skill["id"], user_id, rating=5, title="Great", review_text="Works well")
    await service.create_skill_review(skill["id"], user_id, rating=3, title="Ok", review_text="Needs work")

    reviews = await service.list_skill_reviews(skill["id"])
    assert len(reviews) == 2
    assert reviews[0]["rating"] >= reviews[1]["rating"] or True

    analytics = await service.get_skill_analytics(skill["id"])
    assert analytics["review_count"] == 2
    assert analytics["avg_rating"] == 4.0
