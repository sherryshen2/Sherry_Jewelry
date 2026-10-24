from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from hangarkit.integrations import order_admin

router = APIRouter(prefix="/order-admin", tags=["order-admin"])


class Target(BaseModel):
    env: Literal["uat", "live", "stable", "staging", "test"]
    region: Literal["sg", "ar", "br", "cl", "co", "id", "kh", "la", "mm", "mx", "my", "ph", "th", "tw", "vn", "xx"]


class OrderSearch(Target):
    order_key: str = Field(default="", max_length=64)
    buyer_name: str = Field(default="", max_length=128)
    seller_name: str = Field(default="", max_length=128)
    courier: str = Field(default="", max_length=128)
    cross_border: bool | None = None
    be_status: int | None = Field(default=None, ge=0)
    fe_status: int | None = Field(default=None, ge=0)
    payment_method: int | None = Field(default=None, ge=0)
    checkout_id: int | None = Field(default=None, ge=0)
    shop_id: int | None = Field(default=None, ge=0)
    ctime_gte: int | None = Field(default=None, ge=0, le=4102444800)
    ctime_lte: int | None = Field(default=None, ge=0, le=4102444800)
    mtime_gte: int | None = Field(default=None, ge=0, le=4102444800)
    mtime_lte: int | None = Field(default=None, ge=0, le=4102444800)
    offset: int = Field(default=0, ge=0, le=10000)

    @model_validator(mode="after")
    def validate_date_ranges(self):
        for prefix in ("ctime", "mtime"):
            start = getattr(self, f"{prefix}_gte")
            end = getattr(self, f"{prefix}_lte")
            if start is not None and end is not None and start > end:
                raise ValueError(f"{prefix} start must be before end.")
        return self


def _entries(payload):
    if not isinstance(payload, dict) or payload.get("success") is False:
        raise ValueError("Order Admin returned an unsuccessful response.")
    for _ in range(3):
        if "order_list" in payload or "has_more" in payload:
            break
        payload = payload.get("result") or payload.get("data")
        if not isinstance(payload, dict):
            raise ValueError("Order Admin returned an unexpected response.")
    if payload.get("error_msg"):
        raise ValueError("Order Admin rejected the search.")
    orders = payload.get("order_list", [])
    if not isinstance(orders, list) or any(not isinstance(order, dict) for order in orders):
        raise ValueError("Order Admin returned an unexpected order list.")
    ids = ("order_id", "checkout_id", "shop_id")
    return {
        "orders": [
            {
                **{key: str(order[key]) if order.get(key) is not None else None for key in ids},
                **{key: order.get(key) for key in (
                "order_id", "order_sn", "checkout_id", "buyer_name", "seller_name",
                "shop_id", "be_status", "fe_status", "payment_method", "courier",
                "fulfilment_channel", "currency", "grand_total", "ctime", "mtime",
                "cross_border",
                ) if key not in ids},
            } for order in orders
        ],
        "has_more": bool(payload.get("has_more", False)),
    }


def _search(target: OrderSearch):
    body = {"limit": 20, "offset": target.offset}
    for key in ("buyer_name", "seller_name", "courier"):
        value = getattr(target, key).strip()
        if value:
            body[key] = value
    for key in (
        "cross_border", "be_status", "fe_status", "payment_method", "checkout_id",
        "shop_id", "ctime_gte", "ctime_lte", "mtime_gte", "mtime_lte",
    ):
        value = getattr(target, key)
        if value is not None:
            body[key] = value

    order_key = target.order_key.strip()
    if order_key:
        body["order_id" if order_key.isascii() and order_key.isdecimal() else "order_sn"] = (
            int(order_key) if order_key.isascii() and order_key.isdecimal() else order_key
        )
    result = _entries(order_admin.call("query-order-list-with-filters", env=target.env, region=target.region, json=body))
    # A numeric SN is indistinguishable from an ID in a single field; retry by SN only when ID has no match.
    if order_key and "order_id" in body and not result["orders"] and target.offset == 0:
        sn_body = {key: value for key, value in body.items() if key != "order_id"}
        sn_body["order_sn"] = order_key
        result = _entries(order_admin.call("query-order-list-with-filters", env=target.env, region=target.region, json=sn_body))
    return {"orders": result["orders"], "has_more": result["has_more"], "offset": target.offset, "limit": 20}


@router.post("/access")
def check_access(target: Target):
    try:
        return order_admin.ensure_access(env=target.env, region=target.region)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Order Admin access could not be checked right now. Please try again.",
        ) from exc


@router.post("/search")
def search_orders(target: OrderSearch):
    try:
        return _search(target)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Order search did not complete. Check access for this target, then try again.",
        ) from exc
