from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    vendor_id: int | None
    permissions: list[str]
    default_redirect: str

    model_config = {"from_attributes": True}
