import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import motor.motor_asyncio
from pymongo import ObjectId

app = FastAPI(title="Qarz Daftar API")

# Frontend xavfsiz ulanishi uchun CORS sozlamasi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MONGODB GA ULANISH (RENDER UCHUN TO`G`RI VARIANT) ---
# Render dagi Environment Variables bo'limidan MONGO_URI ni qidiradi, 
# Agar topolmasa lokal bazaga ulanadi.
MONGO_DETAILS = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.qarz_daftar
debt_collection = database.get_collection("debts")


# ---- ENUMLAR ----
class TuriEnum(str, Enum):
    qarz_oldim = "qarz_oldim"
    qarz_berdim = "qarz_berdim"

class HolatEnum(str, Enum):
    tolanmagan = "tolanmagan"
    qisman_tolangan = "qisman_tolangan"
    uzildi = "uzildi"


# ---- PYDANTIC MODELLARI ----
class DebtSchema(BaseModel):
    ism: str = Field(..., min_length=2)
    summa: float = Field(..., gt=0)
    turi: TuriEnum
    izoh: Optional[str] = ""
    holat: HolatEnum = HolatEnum.tolanmagan
    sana: datetime = Field(default_factory=datetime.utcnow)

class UpdateDebtSchema(BaseModel):
    ism: Optional[str] = None
    summa: Optional[float] = None
    turi: Optional[TuriEnum] = None
    izoh: Optional[str] = None
    holat: Optional[HolatEnum] = None


# ---- YORDAMCHI FUNKSIYA ----
def debt_helper(debt) -> dict:
    return {
        "id": str(debt["_id"]),
        "ism": debt["ism"],
        "summa": debt["summa"],
        "turi": debt["turi"],
        "izoh": debt.get("izoh", ""),
        "holat": debt.get("holat", "tolanmagan"),
        "sana": debt["sana"].isoformat() if isinstance(debt["sana"], datetime) else debt["sana"]
    }


# ================= API RO`YTARLARI (CRUD) =================

@app.get("/")
async def root():
    return {"xabar": "Qarz Daftar API muvaffaqiyatli ishlayapti!"}

@app.get("/api/debts")
async def get_debts():
    debts = []
    async for debt in debt_collection.find().sort("sana", -1):
        debts.append(debt_helper(debt))
    return debts

@app.get("/api/debts/{id}")
async def get_debt(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID noto'g'ri formatda")
    debt = await debt_collection.find_one({"_id": ObjectId(id)})
    if debt:
        return debt_helper(debt)
    raise HTTPException(status_code=404, detail="Qarz topilmadi")

@app.post("/api/debts", status_code=status.HTTP_201_CREATED)
async def add_debt(debt: DebtSchema):
    debt_dict = debt.model_dump()
    new_debt = await debt_collection.insert_one(debt_dict)
    created_debt = await debt_collection.find_one({"_id": new_debt.inserted_id})
    return debt_helper(created_debt)

@app.put("/api/debts/{id}")
async def update_debt(id: str, req: UpdateDebtSchema):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID noto'g'ri formatda")
    req_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if len(req_data) >= 1:
        await debt_collection.update_one({"_id": ObjectId(id)}, {"$set": req_data})
    existing_debt = await debt_collection.find_one({"_id": ObjectId(id)})
    if existing_debt:
        return debt_helper(existing_debt)
    raise HTTPException(status_code=404, detail="Qarz topilmadi")

@app.delete("/api/debts/{id}")
async def delete_debt(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID noto'g'ri formatda")
    delete_result = await debt_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return {"xabar": "Qarz muvaffaqiyatli o'chirildi"}
    raise HTTPException(status_code=404, detail="Qarz topilmadi")