from fastapi import FastAPI
from database import create_all_tables, get_db
import dishes.router, orders.router
from models import Order
import random
from datetime import datetime, timedelta
import asyncio

app = FastAPI()

create_all_tables()

app.include_router(dishes.router.router, prefix="/dishes", tags=["dishes"])
app.include_router(orders.router.router, prefix="/orders", tags=["orders"])

async def process_orders():
    while True:
        db = next(get_db())
        pending_orders = db.query(Order).filter(Order.status == 'pending').all()

        for order in pending_orders:
            order.status = 'in_progress'
            db.add(order)
        
        db.commit()

        await asyncio.sleep(random.randint(3, 5))

        in_progress_orders = db.query(Order).filter(Order.status == 'in_progress').all()
        for order in in_progress_orders:
            order.status = 'completed'
            db.add(order)
        
        db.commit()

        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_orders())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
