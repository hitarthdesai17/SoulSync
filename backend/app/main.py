from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import messages,companions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(messages.router)
app.include_router(companions.router)

@app.get("/")
def read_root():
    return {"message": "SoulSync backend is alive"}
