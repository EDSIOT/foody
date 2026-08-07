from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(title="Foody API", version="0.1.0")

# CORS pour autoriser ton futur frontend Nuxt (en dev, sur localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # à restreindre en prod
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok", "service": "foody-api"}