"""Tiny notes API with ONE deliberate bug, used only to test the APIGuard GitHub Action.
Do not deploy. The bug: GET /notes/{note_id} never checks who owns the note (BOLA / IDOR)."""
import uuid
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

USERS = {"alice": "alice-test-pw", "bob": "bob-test-pw"}  # test-only accounts
TOKENS: dict[str, str] = {}
NOTES: dict[str, dict] = {}
app = FastAPI(title="Notes test API")


class Login(BaseModel):
    username: str
    password: str


class NoteIn(BaseModel):
    text: str


def current_user(authorization: Optional[str]) -> str:
    user = TOKENS.get((authorization or "").removeprefix("Bearer "))
    if not user:
        raise HTTPException(401, "not logged in")
    return user


@app.post("/login")
def login(body: Login):
    if USERS.get(body.username) != body.password:
        raise HTTPException(401, "bad credentials")
    token = uuid.uuid4().hex
    TOKENS[token] = body.username
    return {"token": token, "user_id": body.username}


@app.post("/notes", status_code=201)
def create_note(body: NoteIn, authorization: Optional[str] = Header(None)):
    user = current_user(authorization)
    note_id = uuid.uuid4().hex
    NOTES[note_id] = {"id": note_id, "owner_id": user, "owner_email": f"{user}@example.com", "text": body.text}
    return NOTES[note_id]


@app.get("/notes/{note_id}")
def get_note(note_id: str, authorization: Optional[str] = Header(None)):
    user = current_user(authorization)
    note = NOTES.get(note_id)
    if not note or note["owner_id"] != user:  # fixed: only the owner can read a note
        raise HTTPException(404, "not found")
    return note
