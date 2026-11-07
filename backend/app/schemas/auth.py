from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    """Login with email or mobile. `email` kept for API compat; `login` preferred."""

    password: str = Field(min_length=1)
    email: str | None = Field(default=None, max_length=150)
    login: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def require_identifier(self):
        ident = (self.login or self.email or "").strip()
        if not ident:
            raise ValueError("Email or mobile number is required")
        # Normalize onto email so auth.login can keep using body.email
        self.email = ident
        return self


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    vendor_id: int | None
    permissions: list[str]
    default_redirect: str

    model_config = {"from_attributes": True}
