from fastapi import FastAPI, HTTPException, Query, status, Response
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, select, Field
from app.utils import string_analyzer
from app.deps import SessionDep
from app.db import create_db_and_tables
from app.models import StringResponse, DataEntry, Properties
from app.utils import now_isoutc, generate_sha256, parse_nl_query
from pydantic import BaseModel
from json import JSONDecodeError




class StringIn(BaseModel):
    value: str = Field(..., min_length=1, description="String to analyze (non-empty)")

app = FastAPI()


@app.post("/strings", status_code=status.HTTP_201_CREATED, response_model=StringResponse)
async def analyze_string(string: StringIn, session: SessionDep):

    try:
        body = await string.model_dump()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid json body")
    if 'value' not in body:
        raise HTTPException(status_code=400, detail='Invalid request body or missing "value" field')
    value = body['value']

    if not isinstance(value, str):
        raise HTTPException(status_code=422, detail=" Invalid data type for 'value' (must be string)")

    props = string_analyzer(value)
    hashed_value = props.sha256_hash
    existing = session.exec(select(DataEntry).where(DataEntry.sha256_hash == hashed_value)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="String already exists in the system")
    
    data_entry = DataEntry(
        id = props.sha256_hash, 
        value = value,
        length = props.length,
        is_palindrome = props.is_palindrome,
        unique_characters = props.unique_characters,
        sha256_hash = props.sha256_hash,
        word_count = props.word_count,
        character_frequency_map = props.character_frequency_map,
        created_at = now_isoutc()
    )

    session.add(data_entry)
    session.commit()
    session.refresh(data_entry)

    response_data = StringResponse(
        id=data_entry.id,
        value=data_entry.value,
        properties=props,
        created_at=data_entry.created_at
    )
    
    
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_201_CREATED
    )


@app.get("/strings/filter-by-natural-language")
def filter_nl(
    session: SessionDep,
    query: str = Query(..., description="Natural language query"),
):
    try:
        parsed = parse_nl_query(query)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse natural language query"
        )

    if (
        "min_length" in parsed
        and "max_length" in parsed
        and parsed["min_length"] > parsed["max_length"]
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Query parsed but resulted in conflicting filters"
        )

    q = select(DataEntry)
    
    if parsed.get("is_palindrome") is True:
        q = q.where(DataEntry.is_palindrome == True)
    
    if parsed.get("min_length") is not None:
        q = q.where(DataEntry.length >= parsed["min_length"])
    if parsed.get("max_length") is not None:
        q = q.where(DataEntry.length <= parsed["max_length"])
    
    if parsed.get("word_count") is not None:
        q = q.where(DataEntry.word_count == parsed["word_count"])

    rows = session.exec(q).all()

    
    if parsed.get("contains_character"):
        ch = parsed["contains_character"].lower()
        
        filtered = []
        for r in rows:
            freq_map = r.character_frequency_map or {}
            keys_lower = {str(k).lower() for k in freq_map.keys()}
            if ch in keys_lower:
                filtered.append(r)
        rows = filtered

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No records matched the interpreted natural language filters"
        )

    matching_string = [s.value for s in rows]

    return {
        "data": matching_string,
        "count": len(matching_string),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed,
        },
    }



@app.get("/strings/{string_value}", status_code=status.HTTP_200_OK, response_model=StringResponse)
def read_string(string_value: str, session: SessionDep): 
    sha256_hash = generate_sha256(string_value)
    data = session.exec(select(DataEntry).where(DataEntry.sha256_hash == sha256_hash)).first() 
    if data is None: 
        raise HTTPException(status_code=404, detail="String does not exist in the system") 
    props = Properties(
        length = data.length, 
        is_palindrome = data.is_palindrome, 
        unique_characters = data.unique_characters, 
        sha256_hash = data.sha256_hash, 
        word_count = data.word_count, 
        character_frequency_map = data.character_frequency_map
    )

    response_data = StringResponse(
        id=data.id, 
        value=data.value, 
        properties=props, 
        created_at=data.created_at 
    )  

    return response_data



@app.get("/strings")
def get_all_strings(
    session: SessionDep,
    is_palindrome: bool | None = Query(None),
    min_length: int | None = Query(None, ge=0),
    max_length: int | None = Query(None, ge=0),
    word_count: int | None = Query(None, ge=0),
    contains_character: str | None = Query(None),
):
    try:
        if min_length is not None and max_length is not None and min_length > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query parameter values or types",
            )

        statement = select(DataEntry)

        if is_palindrome is not None:
            statement = statement.where(DataEntry.is_palindrome == is_palindrome)
        if min_length is not None:
            statement = statement.where(DataEntry.length >= min_length)
        if max_length is not None:
            statement = statement.where(DataEntry.length <= max_length)
        if word_count is not None:
            statement = statement.where(DataEntry.word_count == word_count)
        if contains_character is not None:
            # allow case-insensitive contains on the text value (fast) as a fallback
            statement = statement.where(DataEntry.value.ilike(f"%{contains_character}%"))

        result = session.exec(statement).all()
        count = len(result)

        data = []
        for row in result:
            props = Properties(
                length=row.length,
                is_palindrome=row.is_palindrome,
                unique_characters=row.unique_characters,
                word_count=row.word_count,
                sha256_hash=row.sha256_hash,
                character_frequency_map=row.character_frequency_map,
            )
            response_data = StringResponse(
                id=row.id,
                value=row.value,
                properties=props,
                created_at=row.created_at,
            )
            data.append(response_data)

        return {
            "data": data,
            "count": count,
            "filters_applied": {
                "is_palindrome": is_palindrome,
                "min_length": min_length,
                "max_length": max_length,
                "word_count": word_count,
                "contains_character": contains_character,
            },
        }

    except Exception:
        # Keep error message generic but return 400 as before
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query parameter values or types",
        )



@app.delete("/strings/{string_value}", status_code=204)
def delete_string(session: SessionDep, string_value: str):
    hashed_value = generate_sha256(string_value)

    db_obj = session.exec(select(DataEntry).where(DataEntry.sha256_hash == hashed_value)).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    session.delete(db_obj)
    session.commit()
    return Response(status_code=204)






@app.on_event("startup")
def on_startup():
    create_db_and_tables()