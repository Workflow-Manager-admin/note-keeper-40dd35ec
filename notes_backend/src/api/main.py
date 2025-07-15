from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from src.api import models, schemas, auth, database
from typing import List

app = FastAPI(
    title="Notes FastAPI Backend",
    version="1.0.0",
    description="API for notes CRUD with Auth, search, and user management"
)

openapi_tags = [
    {"name": "auth", "description": "User registration and authentication"},
    {"name": "notes", "description": "Note CRUD and search"},
    {"name": "users", "description": "User information"},
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTH ROUTES ---

# PUBLIC_INTERFACE
@app.post("/auth/register", response_model=schemas.UserRead, tags=["auth"], summary="Register a new user", description="Creates a new user with username, email, and password.")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    db_user = db.query(models.User).filter((models.User.email == user.email) | (models.User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email or username already registered.")
    hashed_pw = auth.get_password_hash(user.password)
    user_obj = models.User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

# PUBLIC_INTERFACE
@app.post("/auth/token", response_model=schemas.Token, tags=["auth"], summary="Obtain JWT access token")
def login_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and get JWT token.
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# --- USER INFO ---
# PUBLIC_INTERFACE
@app.get("/users/me", response_model=schemas.UserRead, tags=["users"], summary="Get current user info")
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    Returns the current authenticated user's information.
    """
    return current_user

# --- NOTES CRUD ---

# PUBLIC_INTERFACE
@app.post("/notes/", response_model=schemas.NoteRead, tags=["notes"], summary="Create a new note")
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Creates a note for the authenticated user.
    """
    note_obj = models.Note(**note.dict(), user_id=current_user.id)
    db.add(note_obj)
    db.commit()
    db.refresh(note_obj)
    return note_obj

# PUBLIC_INTERFACE
@app.get("/notes/", response_model=List[schemas.NoteRead], tags=["notes"], summary="List all notes (by user, ordered by last_edited desc)")
def list_notes(skip: int = 0, limit: int = 20, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Returns all notes of the current user, sorted by most recent modification.
    """
    notes = db.query(models.Note).filter(models.Note.user_id == current_user.id).order_by(models.Note.last_edited.desc()).offset(skip).limit(limit).all()
    return notes

# PUBLIC_INTERFACE
@app.get("/notes/{note_id}", response_model=schemas.NoteRead, tags=["notes"], summary="Get a note by ID")
def read_note(note_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Gets a single note by id, if owned by the current user.
    """
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note

# PUBLIC_INTERFACE
@app.put("/notes/{note_id}", response_model=schemas.NoteRead, tags=["notes"], summary="Update a note")
def update_note(note_id: int, note: schemas.NoteUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Updates a note by id, if owned by the user.
    """
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == current_user.id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found.")
    if note.title:
        db_note.title = note.title
    if note.content:
        db_note.content = note.content
    db.commit()
    db.refresh(db_note)
    return db_note

# PUBLIC_INTERFACE
@app.delete("/notes/{note_id}", status_code=204, tags=["notes"], summary="Delete a note")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Deletes a note by id, if owned by the user.
    """
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == current_user.id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found.")
    db.delete(db_note)
    db.commit()
    return

# PUBLIC_INTERFACE
@app.get("/notes/search/", response_model=List[schemas.NoteRead], tags=["notes"], summary="Search notes")
def search_notes(q: str = Query(..., description="Search string in title or content"), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Search notes for current user by substring match in title or content, returns them ordered by `last_edited` desc.
    """
    notes = db.query(models.Note).filter(
        models.Note.user_id == current_user.id,
        (models.Note.title.ilike(f"%{q}%")) | (models.Note.content.ilike(f"%{q}%"))
    ).order_by(models.Note.last_edited.desc()).all()
    return notes

# HEALTH CHECK (existing)
@app.get("/", tags=["users"])
def health_check():
    """API health check endpoint."""
    return {"message": "Healthy"}

# DB initialization
@app.on_event("startup")
def on_startup():
    database.Base.metadata.create_all(bind=database.engine)
