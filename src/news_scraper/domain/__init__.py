"""News scrape domain configuration for self-healing-scraper."""

from self_healing_scraper import DomainPrompts, ScrapeDomain

from news_scraper.domain.prompts import (
    CREATE_SYSTEM,
    CREATE_USER_TEMPLATE,
    REPAIR_SYSTEM,
    REPAIR_USER_TEMPLATE,
)
from news_scraper.domain.validators import NEWS_EXTRA_VALIDATORS, NEWS_KNOWN_CHECKS

NEWS_DOMAIN = ScrapeDomain(
    prompts=DomainPrompts(
        create_system=CREATE_SYSTEM,
        create_user_template=CREATE_USER_TEMPLATE,
        repair_system=REPAIR_SYSTEM,
        repair_user_template=REPAIR_USER_TEMPLATE,
    ),
    default_required_fields=["title", "url"],
    known_checks=NEWS_KNOWN_CHECKS,
    extra_validators=NEWS_EXTRA_VALIDATORS,
)

__all__ = ["NEWS_DOMAIN"]
