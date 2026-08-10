from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, claim, group, user

app = FastAPI(title="design your destiny API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(claim.router, prefix="/claim", tags=["Claims"])
app.include_router(group.router, prefix="/group", tags=["Groups"])

@app.get("/")
def root():
    return {"message": "Welcome to design your destiny backend"}