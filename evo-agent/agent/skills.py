"""Skill persistence and search — thin wrapper around the memory store."""

from agent.memory import save_skill, search_skills, update_skill_stats

__all__ = ["save_skill", "search_skills", "update_skill_stats"]
