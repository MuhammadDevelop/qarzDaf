from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import motor.motor_asyncio
from bson import ObjectId

app = FastAPI(title="Qarz Daftar API")

# Fronted xavfsiz ulanishi uchun CORS sozlamasi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend manzili (masalan: ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB ga ulanish (Lokal yoki MongoDB Atlas ssilkasi)
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.qarz_daftar
debt_collection = database.get_collection("debts")


# ---- ENUMLAR (Turlar va Holatlar) ----
class TuriEnum(str, Enum):
    qarz_oldim = "qarz_oldim"
    qarz_berdim = "qarz_berdim"

class HolatEnum(str, Enum):
    tolanmagan = "tolanmagan"
    qisman_tolangan = "qisman_tolangan"
    uzildi = "uzildi"


# ---- PYDANTIC MODELLARI (Ma'lumotlar tuzilishi) ----
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
# MongoDB dagi _id ni string formatga o'tkazish uchun
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

# 1. Barcha qarzlarni olish (GET)
@app.get("/api/debts", response_description="Barcha qarzlar ro'yxati")
async def get_debts():
    debts = []
    # Qarzlarni sanasi bo'yicha eng yangisini birinchi qilib saralaymiz
    async for debt in debt_collection.find().sort("sana", -1):
        debts.append(debt_helper(debt))
    return debts


# 2. Yangi qarz qo'shish (POST)
@app.get("/api/debts/{id}", response_description="Bitta qarz ma'lumoti")
async def get_debt(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID noto'g'ri formatda")
    
    debt = await debt_collection.find_one({"_id": ObjectId(id)})
    if debt:
        return debt_helper(debt)
    raise HTTPException(status_code=404, detail="Qarz topilmadi")


@app.post("/api/debts", status_code=status.HTTP_201_CREATED, response_description="Yangi qarz saqlandi")
async def add_debt(debt: DebtSchema):
    debt_dict = debt.model_dump()
    new_debt = await debt_collection.insert_one(debt_dict)
    created_debt = await debt_collection.find_one({"_id": new_debt.inserted_id})
    return debt_helper(created_debt)


# 3. Qarzni tahrirlash / Yangilash (PUT)
@app.put("/api/debts/{id}", response_description="Qarz tahrirlandi")
async def update_debt(id: str, req: UpdateDebtSchema):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID noto'g'ri formatda")

    # Faqat jo'natilgan (None bo'lmagan) maydonlarni ajratib olamiz
    req_data = {k: v for k, v in req.model_dump().items() if v is not None}
    
    if len(req_data) >= 1:
        update_result = await debt_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": req_data}
        )
        if update_result.modified_count == 1:
            updated_debt = await debt_collection.find_one({"_id": ObjectId(id)})
            return debt_helper(updated_debt)

    # Agar o'zgarish bo'lmasa eski ma'lumotni qaytaramiz
    existing_debt = await debt_collection.find_one({"_id": ObjectId(id)})
    if existing_debt:
        return debt_helper(existing_debt)
    
    raise HTTPException(status_code=404, detail="Qarz topilmadi")


# 4. Qarzni o'chirish (DELETE)
@app.delete("/api/debts/{id}", response_description="Qarz o'chirildi")
async def delete_debt(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID noto'g'ri formatda")

    delete_result = await debt_collection.delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 1:
        return {"xabar": "Qarz muvaffaqiyatli o'chirildi"}
        
    raise HTTPException(status_code=404, detail="Qarz topilmadi")