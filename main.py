'''
TASK 8:

models all in app>models>user.py
socket server in app>dependencies>socketz.py
some api endpoints does not work in defult api view in browser (localhost:8000/docs#/) need to use postman

added two routes for testing remove-user-from-patient and add-user-to-patient

'''
from fastapi import FastAPI
from app.dependencies.database import init_tortoise, close_tortoise
from app.routes import user_routes, system_routes
from fastapi.middleware.cors import CORSMiddleware
from app.dependencies.socketz import sio_app


app = FastAPI()

app.include_router(user_routes.router, prefix="/users", tags=["users"])
app.include_router(system_routes.router, prefix="/system", tags=["system"])

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_db():
    await init_tortoise(app)

@app.on_event("shutdown")
async def shutdown_db():
    await close_tortoise(app)

app.mount('/', app=sio_app)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
