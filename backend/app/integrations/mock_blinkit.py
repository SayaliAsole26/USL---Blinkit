from sqlalchemy.orm import Session

from app.db.models import CatalogProduct, ProductAvailability
from app.integrations.base import CatalogAdapter, CatalogProductDTO, CartAdapter, CartItemDTO, InventoryAdapter, OrderAdapter


class MockCatalogAdapter(CatalogAdapter):
    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str, limit: int = 20) -> list[CatalogProductDTO]:
        pattern = f"%{query.lower()}%"
        rows = (
            self.db.query(CatalogProduct)
            .filter(CatalogProduct.product_name.ilike(pattern))
            .limit(limit)
            .all()
        )
        return [_to_dto(r) for r in rows]

    def get_by_sku(self, sku_id: str) -> CatalogProductDTO | None:
        row = self.db.query(CatalogProduct).filter(CatalogProduct.sku_id == sku_id).first()
        return _to_dto(row) if row else None


class MockInventoryAdapter(InventoryAdapter):
    def __init__(self, db: Session):
        self.db = db

    def check_availability(self, sku_id: str, pincode: str) -> str:
        row = (
            self.db.query(ProductAvailability)
            .filter(ProductAvailability.sku_id == sku_id, ProductAvailability.pincode == pincode)
            .first()
        )
        if not row:
            return "unknown"
        return row.availability_status


class MockCartAdapter(CartAdapter):
    def __init__(self):
        self._carts: dict[str, list[CartItemDTO]] = {}

    def get_cart(self, user_id: str, session_id: str | None = None) -> list[CartItemDTO]:
        return list(self._carts.get(user_id, []))

    def add_item(self, user_id: str, sku_id: str, quantity: int = 1) -> bool:
        cart = self._carts.setdefault(user_id, [])
        for item in cart:
            if item.sku_id == sku_id:
                item.quantity += quantity
                return True
        cart.append(CartItemDTO(sku_id=sku_id, quantity=quantity))
        return True


class MockOrderAdapter(OrderAdapter):
    def subscribe_order_completed(self, handler: callable) -> None:
        # Phase 0: no-op; Celery worker will wire this in Phase 3
        pass


def _to_dto(row: CatalogProduct) -> CatalogProductDTO:
    return CatalogProductDTO(
        sku_id=row.sku_id,
        product_name=row.product_name,
        category=row.category,
        price=float(row.price),
        image_url=row.image_url,
    )


_cart_adapter = MockCartAdapter()


def get_cart_adapter() -> MockCartAdapter:
    return _cart_adapter
