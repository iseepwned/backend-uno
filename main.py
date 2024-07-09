from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from controllers import match_controller

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(match_controller.match_controller)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_methods=["*"],
    allow_headers=["*"]
)