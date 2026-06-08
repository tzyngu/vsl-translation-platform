from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class GestureCreate(BaseModel):
    label_name: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    is_public: bool = False


class TranslateRequest(BaseModel):
    labels: list[str] = Field(default_factory=list, max_length=100)

