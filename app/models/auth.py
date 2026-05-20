import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB  # Native Postgres Binary JSON Component
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    TENANT_MODERATOR = "TENANT_MODERATOR"
    END_USER = "END_USER"

# ==============================================================================
# 🏢 TENANT ENGINE MODEL (B2B Multi-Tenancy Core)
# ==============================================================================
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ⚡ CASCADE CONTROL: Tenant delete hoga toh users soft/hard delete handle honge database level par
    users: Mapped[List["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


# ==============================================================================
# 👥 HYBRID USER MODEL (Unified Architecture with Retention Guard)
# ==============================================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.END_USER, server_default="END_USER", nullable=False, index=True)
    
    # ⚙️ SYSTEM LIFECYCLE FLAGS
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Account toggle (Deactivate feature)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False) # Email validation checkpoint
    
    # 🔒 SOFT DELETE & RETENTION ARMOR
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="FALSE", index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True) # Celery/Cron target tracker

    # ⚡ FLEXIBLE METADATA PROFILE (JSONB)
    # Student: {"class": "12th", "batch": "JEE-2026", "roll_no": 42}
    # Teacher: {"subjects": ["Physics"], "experience_years": 8}
    profile_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict, server_default='{}', nullable=True)
    
    # TIMESTAMPS
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tenant: Mapped[Optional["Tenant"]] = relationship(back_populates="users")