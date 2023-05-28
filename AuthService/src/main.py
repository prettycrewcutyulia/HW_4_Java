from fastapi import FastAPI
from database import create_all_tables, get_db
import users.router, sessions.router


app = FastAPI()

create_all_tables()

app.include_router(users.router.router, prefix="/users", tags=["users"])
app.include_router(sessions.router.router, prefix="/sessions", tags=["sessions"])

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)