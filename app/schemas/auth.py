import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from app.models.auth import UserRole

#  INPUT SCHEMAS (Request Payloads)
class TenantCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Alpha Institute"])
    subdomain: str = Field(..., min_length=2, max_length=50, examples=["alpha"])

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = None
    role: UserRole = UserRole.END_USER
    profile_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Optional parameters naya tenant onboard karne ke liye (Tenant Admin flow)
    tenant_details: Optional[TenantCreateSchema] = None

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

#  OUTPUT SCHEMAS (Response Payloads)
class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class UserResponseSchema(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    
    class Config:
        from_attributes = True
        
class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str = Field(..., min_length=10)
    