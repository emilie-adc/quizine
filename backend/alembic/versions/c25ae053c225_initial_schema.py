"""initial schema

Revision ID: c25ae053c225
Revises:
Create Date: 2026-04-08

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = 'c25ae053c225'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'certifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('level', sa.String(50), nullable=False),
        sa.Column('pass_score_pct', sa.Integer(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('prompt_context', sa.Text(), nullable=False),
    )
    op.create_index('ix_certifications_slug', 'certifications', ['slug'])

    op.create_table(
        'cert_domains',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cert_id', sa.Integer(), sa.ForeignKey('certifications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('weight_pct', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
    )
    op.create_index('ix_cert_domains_cert_id', 'cert_domains', ['cert_id'])

    op.create_table(
        'decks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cert_id', sa.Integer(), sa.ForeignKey('certifications.id', ondelete='SET NULL'), nullable=True),
        sa.Column('custom_cert_name', sa.String(200), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_decks_cert_id', 'decks', ['cert_id'])

    op.create_table(
        'source_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('deck_id', sa.Integer(), sa.ForeignKey('decks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_source_chunks_deck_id', 'source_chunks', ['deck_id'])

    op.create_table(
        'cards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('deck_id', sa.Integer(), sa.ForeignKey('decks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_chunk_id', sa.Integer(), sa.ForeignKey('source_chunks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('front', sa.Text(), nullable=True),
        sa.Column('back', sa.Text(), nullable=True),
        sa.Column('custom_topic_tag', sa.String(100), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_cards_deck_id', 'cards', ['deck_id'])

    op.create_table(
        'mcq_options',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('card_id', sa.Integer(), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
    )
    op.create_index('ix_mcq_options_card_id', 'mcq_options', ['card_id'])

    op.create_table(
        'card_tags',
        sa.Column('card_id', sa.Integer(), sa.ForeignKey('cards.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('domain_id', sa.Integer(), sa.ForeignKey('cert_domains.id', ondelete='CASCADE'), primary_key=True),
    )

    op.create_table(
        'card_schedule',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('card_id', sa.Integer(), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('ease_factor', sa.Float(), nullable=False, server_default='2.5'),
        sa.Column('due_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'card_reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('card_id', sa.Integer(), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_card_reviews_card_id', 'card_reviews', ['card_id'])

    op.create_table(
        'exam_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('deck_id', sa.Integer(), sa.ForeignKey('decks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('score_pct', sa.Float(), nullable=True),
    )
    op.create_index('ix_exam_sessions_deck_id', 'exam_sessions', ['deck_id'])

    op.create_table(
        'exam_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('exam_session_id', sa.Integer(), sa.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('card_id', sa.Integer(), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_option_id', sa.Integer(), sa.ForeignKey('mcq_options.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_exam_answers_exam_session_id', 'exam_answers', ['exam_session_id'])


def downgrade() -> None:
    op.drop_table('exam_answers')
    op.drop_table('exam_sessions')
    op.drop_table('card_reviews')
    op.drop_table('card_schedule')
    op.drop_table('card_tags')
    op.drop_table('mcq_options')
    op.drop_table('cards')
    op.drop_table('source_chunks')
    op.drop_table('decks')
    op.drop_table('cert_domains')
    op.drop_table('certifications')
