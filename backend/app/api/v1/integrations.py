from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.integrations.mock_blinkit import MockCatalogAdapter, MockInventoryAdapter, get_cart_adapter
from app.middleware.auth import get_current_user
from app.pipeline.llm import GroqLLMService
from app.schemas.recommendations import (
    OrderCompletedRequest,
    OrderCompletedResponse,
    OrderHistoryImportRequest,
    OrderHistoryImportResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/catalog/products")
def list_catalog_products(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1),
    pincode: str | None = Query(default=None, pattern=r"^\d{6}$"),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
):
    adapter = MockCatalogAdapter(db)
    products = adapter.list_products(category=category, query=q, limit=limit, pincode=pincode)
    return {"count": len(products), "products": [p.__dict__ for p in products]}


@router.get("/catalog/search")
def search_catalog(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    adapter = MockCatalogAdapter(db)
    products = adapter.search(q, limit=limit)
    return {"query": q, "count": len(products), "products": [p.__dict__ for p in products]}


@router.get("/inventory/check")
def check_inventory(
    sku_id: str,
    pincode: str,
    db: Session = Depends(get_db),
):
    adapter = MockInventoryAdapter(db)
    status_value = adapter.check_availability(sku_id, pincode)
    return {"sku_id": sku_id, "pincode": pincode, "availability_status": status_value}


@router.post("/groq/smoke")
def groq_smoke(settings: Settings = Depends(get_settings)):
    llm = GroqLLMService(settings)
    if not llm.is_configured:
        return {"ok": False, "message": "GROQ_API_KEY not set; using template fallback only"}
    return llm.smoke_test()


class CartItemRequest(BaseModel):
    sku_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)


@router.get("/cart")
def get_cart(user: User = Depends(get_current_user)):
    cart = get_cart_adapter().get_cart(str(user.user_id))
    return {"items": [{"sku_id": i.sku_id, "quantity": i.quantity} for i in cart]}


@router.post("/cart/items")
def add_cart_item(payload: CartItemRequest, user: User = Depends(get_current_user)):
    get_cart_adapter().add_item(str(user.user_id), payload.sku_id, payload.quantity)
    return {"ok": True, "sku_id": payload.sku_id}


@router.post("/orders/completed", response_model=OrderCompletedResponse)
def order_completed(
    payload: OrderCompletedRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    purchased_count, history_count = RecommendationService(db, settings).handle_order_completed(
        user.user_id,
        payload.sku_ids,
        payload.order_id,
    )
    return OrderCompletedResponse(
        order_id=payload.order_id,
        usl_items_marked_purchased=purchased_count,
        purchase_history_recorded=history_count,
    )


@router.post("/orders/history/import", response_model=OrderHistoryImportResponse)
def import_order_history(
    payload: OrderHistoryImportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.purchase_history_service import PurchaseHistoryService

    service = PurchaseHistoryService(db)
    recorded = 0
    for entry in payload.purchases:
        order_id = entry.order_id or f"hist_{recorded}"
        n = service.record_order_purchases(
            user.user_id,
            [entry.sku_id],
            order_id,
            source="blinkit_history",
            purchased_at=entry.purchased_at,
        )
        recorded += n

    db.commit()
    return OrderHistoryImportResponse(recorded=recorded)
