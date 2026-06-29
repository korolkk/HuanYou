"""Initial database schema with all tables and pgvector indexes.

Revision ID: 001
Revises: None
Create Date: 2026-06-29
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # ── customers ──
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("phone", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100)),
        sa.Column("id_number", sa.String(100)),
        sa.Column("gender", sa.String(10)),
        sa.Column("birth_date", sa.Date),
        sa.Column("email", sa.String(255)),
        sa.Column("wechat_id", sa.String(100)),
        sa.Column("emergency_contact", sa.String(100)),
        sa.Column("emergency_phone", sa.String(20)),
        sa.Column("role", sa.String(20), server_default="user", index=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── customer_profiles ──
    op.create_table(
        "customer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("age_group", sa.String(20)),
        sa.Column("city", sa.String(50)),
        sa.Column("occupation_category", sa.String(50)),
        sa.Column("preferred_destinations", postgresql.ARRAY(sa.Text)),
        sa.Column("preferred_categories", postgresql.ARRAY(sa.Text)),
        sa.Column("budget_range_min", sa.Float),
        sa.Column("budget_range_max", sa.Float),
        sa.Column("preferred_duration_days", sa.Integer),
        sa.Column("preferred_season", sa.String(20)),
        sa.Column("preferred_group_size", sa.Integer),
        sa.Column("travel_style", sa.String(50)),
        sa.Column("booking_frequency", sa.String(20)),
        sa.Column("avg_booking_lead_days", sa.Integer),
        sa.Column("cancellation_rate", sa.Float),
        sa.Column("preferred_contact_time", sa.String(20)),
        sa.Column("interest_tags", postgresql.ARRAY(sa.Text)),
        sa.Column("special_requirements", postgresql.ARRAY(sa.Text)),
        sa.Column("mem0_user_id", sa.String(100)),
        sa.Column("profile_summary", sa.Text),
        sa.Column("profile_embedding", Vector(1024)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── trips ──
    op.create_table(
        "trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("subtitle", sa.String(200)),
        sa.Column("destination", sa.String(100), nullable=False, index=True),
        sa.Column("destinations_detail", postgresql.ARRAY(sa.Text)),
        sa.Column("country", sa.String(50), server_default="中国"),
        sa.Column("province", sa.String(50)),
        sa.Column("city", sa.String(50)),
        sa.Column("category", sa.String(30), index=True),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("duration_nights", sa.Integer),
        sa.Column("departure_city", sa.String(50)),
        sa.Column("best_season", sa.String(100)),
        sa.Column("price_adult", sa.Float),
        sa.Column("price_child", sa.Float),
        sa.Column("price_infant", sa.Float),
        sa.Column("single_room_supplement", sa.Float),
        sa.Column("price_includes", postgresql.ARRAY(sa.Text)),
        sa.Column("price_excludes", postgresql.ARRAY(sa.Text)),
        sa.Column("summary", sa.Text),
        sa.Column("highlights", postgresql.ARRAY(sa.Text)),
        sa.Column("recommendation_reasons", postgresql.ARRAY(sa.Text)),
        sa.Column("detailed_description", sa.Text),
        sa.Column("group_size_min", sa.Integer, server_default="1"),
        sa.Column("group_size_max", sa.Integer),
        sa.Column("departure_dates", postgresql.ARRAY(sa.Text)),
        sa.Column("cover_image_url", sa.String(500)),
        sa.Column("image_urls", postgresql.ARRAY(sa.Text)),
        sa.Column("brochure_url", sa.String(500)),
        sa.Column("content_embedding", Vector(1024)),
        sa.Column("status", sa.String(20), server_default="active", index=True),
        sa.Column("is_featured", sa.Boolean, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── trip_schedules ──
    op.create_table(
        "trip_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("day_number", sa.Integer, nullable=False),
        sa.Column("theme", sa.String(100)),
        sa.Column("schedule_type", sa.String(30), server_default="景点"),
        sa.Column("time_start", sa.Time),
        sa.Column("time_end", sa.Time),
        sa.Column("location", sa.String(200)),
        sa.Column("activity", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("meal_included", sa.String(50)),
        sa.Column("hotel_name", sa.String(200)),
        sa.Column("hotel_stars", sa.Integer),
        sa.Column("hotel_description", sa.Text),
        sa.Column("transport_type", sa.String(50)),
        sa.Column("transport_detail", sa.Text),
        sa.Column("tips", sa.Text),
        sa.Column("image_urls", postgresql.ARRAY(sa.Text)),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("schedule_embedding", Vector(1024)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── orders ──
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_code", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("trips.id"), nullable=False, index=True),
        sa.Column("departure_date", sa.Date),
        sa.Column("num_adults", sa.Integer, server_default="1"),
        sa.Column("num_children", sa.Integer, server_default="0"),
        sa.Column("num_infants", sa.Integer, server_default="0"),
        sa.Column("total_price", sa.Float),
        sa.Column("paid_amount", sa.Float, server_default="0.0"),
        sa.Column("discount_amount", sa.Float, server_default="0.0"),
        sa.Column("participants", postgresql.JSONB),
        sa.Column("status", sa.String(30), server_default="inquiry", index=True),
        sa.Column("payment_status", sa.String(30), server_default="unpaid"),
        sa.Column("contract_url", sa.String(500)),
        sa.Column("insurance_url", sa.String(500)),
        sa.Column("reserved_at", sa.DateTime(timezone=True)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("departed_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── video_scripts ──
    op.create_table(
        "video_scripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("trips.id"), nullable=False, index=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("title", sa.String(200)),
        sa.Column("platform", sa.String(50), server_default="抖音"),
        sa.Column("duration_seconds", sa.Integer, server_default="300"),
        sa.Column("script_content", sa.Text, nullable=False),
        sa.Column("script_json", postgresql.JSONB),
        sa.Column("hook_text", sa.Text),
        sa.Column("highlights_text", sa.Text),
        sa.Column("detail_text", sa.Text),
        sa.Column("cta_text", sa.Text),
        sa.Column("image_assignments", postgresql.JSONB),
        sa.Column("quality_score", sa.Float),
        sa.Column("engagement_score", sa.Float),
        sa.Column("accuracy_score", sa.Float),
        sa.Column("generation_version", sa.Integer, server_default="1"),
        sa.Column("polish_iterations", sa.Integer, server_default="0"),
        sa.Column("model_used", sa.String(50)),
        sa.Column("generation_time_ms", sa.Integer),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── conversations ──
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("session_id", sa.String(100), nullable=False, index=True),
        sa.Column("role", sa.String(20)),
        sa.Column("agent_name", sa.String(50)),
        sa.Column("content", sa.Text),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── document_chunks ──
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_file", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("embedding", Vector(1024)),
        sa.Column("search_vector", postgresql.TSVECTOR),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── feedback ──
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("orders.id"), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("rating_overall", sa.Integer),
        sa.Column("rating_guide", sa.Integer),
        sa.Column("rating_accommodation", sa.Integer),
        sa.Column("rating_transport", sa.Integer),
        sa.Column("rating_food", sa.Integer),
        sa.Column("rating_itinerary", sa.Integer),
        sa.Column("positive_points", sa.Text),
        sa.Column("negative_points", sa.Text),
        sa.Column("suggestions", sa.Text),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("staff_response", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── pgvector HNSW indexes ──
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trips_embedding ON trips "
        "USING hnsw (content_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_profiles_embedding ON customer_profiles "
        "USING hnsw (profile_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_schedules_embedding ON trip_schedules "
        "USING hnsw (schedule_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200)"
    )

    # ── GIN indexes for full-text search and JSONB ──
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_search ON document_chunks USING gin(search_vector)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON document_chunks USING gin(metadata)"
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("document_chunks")
    op.drop_table("conversations")
    op.drop_table("video_scripts")
    op.drop_table("orders")
    op.drop_table("trip_schedules")
    op.drop_table("trips")
    op.drop_table("customer_profiles")
    op.drop_table("customers")
