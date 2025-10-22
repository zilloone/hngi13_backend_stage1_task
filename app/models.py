from sqlmodel import SQLModel, Field, Column, JSON
import uuid


class DataEntry(SQLModel, table=True):
    id: str | None = Field(primary_key=True, index=True)
    value: str
    length: int
    is_palindrome: bool = Field(default=False)
    unique_characters: int
    sha256_hash: str
    words_count: int
    character_frequency_map: dict[str, int] = Field(sa_column=Column(JSON))
    created_at: str



class CreateString(SQLModel):
    value: str = Field(description="String to analyze")

class Properties(SQLModel):
    length: int
    is_palindrome: bool 
    unique_characters: int
    words_count: int
    sha256_hash: str
    character_frequency_map: dict[str, int] = Field(sa_column=Column(JSON))
    

class StringResponse(SQLModel):
    id: str
    value: str
    properties: Properties
    created_at: str



    

 


    