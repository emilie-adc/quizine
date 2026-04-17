"""
Seed script: upsert verified certifications from seed/certifications.json.
Idempotent — safe to re-run (upsert by slug, per ADR-009).
Called from main.py lifespan on startup.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.certifications import CertDomain, Certification

SEED_FILE = Path(__file__).parent / "seed" / "certifications.json"


async def seed_certifications(db: AsyncSession) -> None:
    data = json.loads(SEED_FILE.read_text())

    for entry in data:
        result = await db.execute(
            select(Certification)
            .where(Certification.slug == entry["slug"])
            .options(selectinload(Certification.domains))
        )
        cert = result.scalar_one_or_none()

        if cert is None:
            cert = Certification(
                slug=entry["slug"],
                display_name=entry["display_name"],
                provider=entry["provider"],
                level=entry["level"],
                pass_score_pct=entry["pass_score_pct"],
                verified=True,
                prompt_context=entry["prompt_context"],
            )
            db.add(cert)
            await db.flush()  # get cert.id before inserting domains
            existing_domains: dict[str, CertDomain] = {}
        else:
            cert.display_name = entry["display_name"]
            cert.provider = entry["provider"]
            cert.level = entry["level"]
            cert.pass_score_pct = entry["pass_score_pct"]
            cert.prompt_context = entry["prompt_context"]
            # domains were eagerly loaded via selectinload above
            existing_domains = {d.slug: d for d in cert.domains}
        for domain_entry in entry["domains"]:
            domain = existing_domains.get(domain_entry["slug"])
            if domain is None:
                domain = CertDomain(
                    cert_id=cert.id,
                    name=domain_entry["name"],
                    slug=domain_entry["slug"],
                    weight_pct=domain_entry["weight_pct"],
                    description=domain_entry["description"],
                )
                db.add(domain)
            else:
                domain.name = domain_entry["name"]
                domain.weight_pct = domain_entry["weight_pct"]
                domain.description = domain_entry["description"]

    await db.commit()
