from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import routers
import os

if not os.path.exists("./logs"):
    os.mkdir("./logs")

Base.metadata.create_all(bind=engine)
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for router in routers:
    app.include_router(router)
