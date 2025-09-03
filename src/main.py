import os
import aiomysql
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# --- Database Configuration ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "email_subscriptions")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Point to the new 'templates' directory
templates = Jinja2Templates(directory="templates")
db_pool = None

# --- Database Connection Pool & Startup/Shutdown Events (same as before) ---
async def get_db_pool():
    return await aiomysql.create_pool(
        host=DB_HOST, port=3306, user=DB_USER, password=DB_PASSWORD, db=DB_NAME, autocommit=True
    )

@app.on_event("startup")
async def startup_event():
    global db_pool
    try:
        conn = await aiomysql.connect(host=DB_HOST, port=3306, user=DB_USER, password=DB_PASSWORD)
        async with conn.cursor() as cursor:
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.close()
    except Exception as e:
        print(f"Could not connect to MariaDB to create database: {e}")
        return

    db_pool = await get_db_pool()

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    company VARCHAR(255) NOT NULL,
                    subscription_type VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_email_subscription (email, subscription_type)
                )
            """)

@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

# --- Frontend Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# --- API Endpoints ---
@app.post("/register")
async def register_user(
    email: str = Form(...), company: str = Form(...), subscription: List[str] = Form(...), terms: bool = Form(...)
):
    if not terms:
        raise HTTPException(status_code=400, detail="Terms must be accepted")
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database service is not available")

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            for sub_type in subscription:
                try:
                    await cursor.execute(
                        "INSERT INTO subscriptions (email, company, subscription_type) VALUES (%s, %s, %s)",
                        (email, company, sub_type)
                    )
                except aiomysql.IntegrityError:
                    print(f"Subscription already exists for {email} - {sub_type}. Skipping.")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Database insertion error: {e}")

    return JSONResponse(content={"message": "Registration successful!"})

@app.get("/api/subscriptions")
async def get_subscriptions():
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database service is not available")
    
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT id, email, company, subscription_type FROM subscriptions ORDER BY created_at DESC")
            result = await cursor.fetchall()
            return result

@app.delete("/api/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: int):
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database service is not available")

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM subscriptions WHERE id = %s", (subscription_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Subscription not found")
    
    return JSONResponse(content={"message": f"Subscription #{subscription_id} deleted successfully."})
