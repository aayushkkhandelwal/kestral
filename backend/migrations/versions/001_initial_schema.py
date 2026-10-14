"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-15 00:00:00.000000+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    # 2. Cameras Table
    op.create_table(
        "cameras",
        sa.Column("camera_id", sa.UUID(), nullable=False),
        sa.Column("camera_name", sa.String(length=128), nullable=False),
        sa.Column("atm_id", sa.String(length=64), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="online"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("camera_id"),
    )
    op.create_index("ix_cameras_camera_name", "cameras", ["camera_name"])
    op.create_index("ix_cameras_atm_id", "cameras", ["atm_id"])
    op.create_index("ix_cameras_status", "cameras", ["status"])

    # 3. Videos Table
    op.create_table(
        "videos",
        sa.Column("video_id", sa.UUID(), nullable=False),
        sa.Column("camera_id", sa.UUID(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fps", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("resolution", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.camera_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("video_id"),
    )
    op.create_index("ix_videos_camera_id", "videos", ["camera_id"])
    op.create_index("ix_videos_uploaded_by", "videos", ["uploaded_by"])
    op.create_index("ix_videos_processing_status", "videos", ["processing_status"])
    op.create_index("ix_videos_sha256", "videos", ["sha256"])

    # 4. Person Tracks Table
    op.create_table(
        "person_tracks",
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.Column("video_id", sa.UUID(), nullable=False),
        sa.Column("person_number", sa.Integer(), nullable=False),
        sa.Column("start_frame", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_frame", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_frames", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_evidence_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["video_id"], ["videos.video_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("track_id"),
        sa.UniqueConstraint("video_id", "person_number", name="uq_video_person_number"),
    )
    op.create_index("ix_person_tracks_video_id", "person_tracks", ["video_id"])
    op.create_index("ix_person_tracks_person_number", "person_tracks", ["person_number"])
    op.create_index("ix_person_tracks_best_evidence_id", "person_tracks", ["best_evidence_id"])

    # 5. Face Evidence Table
    op.create_table(
        "face_evidence",
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.Column("face_crop_path", sa.String(length=512), nullable=True),
        sa.Column("full_frame_path", sa.String(length=512), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quality_grade", sa.String(length=8), nullable=False, server_default="C"),
        sa.Column("sharpness", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("brightness", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("contrast", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("resolution", sa.String(length=32), nullable=False, server_default="0x0"),
        sa.Column("face_confidence", sa.Float(), nullable=True),
        sa.Column("is_best", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sha256_crop", sa.String(length=64), nullable=True),
        sa.Column("sha256_frame", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["track_id"], ["person_tracks.track_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("evidence_id"),
    )
    op.create_index("ix_face_evidence_track_id", "face_evidence", ["track_id"])
    op.create_index("ix_face_evidence_quality_score", "face_evidence", ["quality_score"])
    op.create_index("ix_face_evidence_quality_grade", "face_evidence", ["quality_grade"])
    op.create_index("ix_face_evidence_is_best", "face_evidence", ["is_best"])
    op.create_index("ix_face_evidence_created_at", "face_evidence", ["created_at"])
    op.create_index(
        "uq_track_best_evidence",
        "face_evidence",
        ["track_id"],
        unique=True,
        postgresql_where=sa.text("is_best = true"),
        sqlite_where=sa.text("is_best = 1")
    )

    # 6. Investigation Cases Table
    op.create_table(
        "investigation_cases",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("case_id"),
    )
    op.create_index("ix_investigation_cases_title", "investigation_cases", ["title"])
    op.create_index("ix_investigation_cases_status", "investigation_cases", ["status"])
    op.create_index("ix_investigation_cases_assigned_to", "investigation_cases", ["assigned_to"])
    op.create_index("ix_investigation_cases_created_by", "investigation_cases", ["created_by"])
    op.create_index("ix_investigation_cases_created_at", "investigation_cases", ["created_at"])

    # 7. Case Evidence Mapping Table
    op.create_table(
        "case_evidence",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("added_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.case_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["face_evidence.evidence_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["added_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("case_id", "evidence_id"),
    )

    # 8. Alerts Table
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.UUID(), nullable=False),
        sa.Column("camera_id", sa.UUID(), nullable=True),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.camera_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("alert_id"),
    )
    op.create_index("ix_alerts_camera_id", "alerts", ["camera_id"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_timestamp", "alerts", ["timestamp"])
    op.create_index("ix_alerts_acknowledged_at", "alerts", ["acknowledged_at"])

    # 9. Audit Logs Table
    op.create_table(
        "audit_logs",
        sa.Column("log_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_table("case_evidence")
    op.drop_table("investigation_cases")
    op.drop_table("face_evidence")
    op.drop_table("person_tracks")
    op.drop_table("videos")
    op.drop_table("cameras")
    op.drop_table("users")
