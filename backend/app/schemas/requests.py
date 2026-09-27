from pydantic import BaseModel, Field, field_validator
from typing import Literal
class Login(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1,max_length=128)
class Register(Login):
    name: str = Field(min_length=2,max_length=100)
    @field_validator('password')
    @classmethod
    def strong(cls,value):
        if len(value)<10: raise ValueError('Use at least 10 characters')
        return value
    @field_validator('email')
    @classmethod
    def email_valid(cls,value):
        if '@' not in value or '.' not in value.split('@')[-1]: raise ValueError('Enter a valid email')
        return value.lower().strip()
class Refresh(BaseModel): refresh_token: str = Field(max_length=200)
class Chat(BaseModel):
    question: str = Field(min_length=3,max_length=4000)
    conversation_id: str | None = None
    document_id: str | None = None
class DocumentEdit(BaseModel):
    title: str | None = Field(default=None,min_length=2,max_length=300)
    region: Literal['Arctic','Antarctic'] | None = None
    domain: str | None = Field(default=None,max_length=100)
    visibility: Literal['public','private'] | None = None
    tags: list[str] | None = Field(default=None,max_length=20)
class Moderate(BaseModel):
    status: Literal['UNDER_REVIEW','APPROVED','REJECTED','PUBLISHED']
    reason: str = Field(default='',max_length=1000)
class Generate(BaseModel):
    document_id: str
    format: Literal['Public awareness article','Social media post','Instagram caption','LinkedIn post','X/Twitter post','Short video script','Educational summary','Press-release draft']='Public awareness article'
    audience: Literal['School students','College students','Researchers','General public','Government officials']='General public'
    tone: Literal['Scientific','Educational','Simple','Professional']='Simple'
class QuizAnswers(BaseModel): answers: list[int] = Field(max_length=100)
class UserEdit(BaseModel):
    role: Literal['public','researcher','content_manager','admin']
    active: bool=True
