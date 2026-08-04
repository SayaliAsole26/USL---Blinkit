from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CatalogProductDTO:
    sku_id: str
    product_name: str
    category: str
    price: float
    image_url: str | None = None


class CatalogAdapter(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[CatalogProductDTO]:
        pass

    @abstractmethod
    def get_by_sku(self, sku_id: str) -> CatalogProductDTO | None:
        pass


class InventoryAdapter(ABC):
    @abstractmethod
    def check_availability(self, sku_id: str, pincode: str) -> str:
        """Returns: available | unavailable | unknown"""
        pass


@dataclass
class CartItemDTO:
    sku_id: str
    quantity: int


class CartAdapter(ABC):
    @abstractmethod
    def get_cart(self, user_id: str, session_id: str | None = None) -> list[CartItemDTO]:
        pass

    @abstractmethod
    def add_item(self, user_id: str, sku_id: str, quantity: int = 1) -> bool:
        pass


class OrderAdapter(ABC):
    @abstractmethod
    def subscribe_order_completed(self, handler: callable) -> None:
        pass
