from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Order, Payment, User
from app.schemas.dto import CheckoutIn, CheckoutResponse, OrderOut, PaymentOut
from app.services.cart_service import get_or_create_cart
from app.services.order_transaction import CheckoutError, OrderCheckoutService

router = APIRouter()


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    body: CheckoutIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(db, user.id)
    svc = OrderCheckoutService(db)
    try:
        order, payment = svc.checkout(
            user_id=user.id,
            cart=cart,
            address_id=body.address_id,
            simulate_failure=body.simulate_failure,
            coupon_code=body.coupon_code,
        )
    except CheckoutError as exc:
        raise HTTPException(400, str(exc)) from exc

    return CheckoutResponse(order=OrderOut.model_validate(order), payment=PaymentOut.model_validate(payment))


@router.get("/mine", response_model=list[OrderOut])
def list_mine(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    return db.scalars(stmt).all()


@router.get("/{order_id}", response_model=OrderOut)
def order_detail(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalars(select(Order).where(Order.id == order_id, Order.user_id == user.id)).one_or_none()
    if order is None:
        raise HTTPException(404, "Order not found")
    return order


@router.get("/{order_id}/payment", response_model=PaymentOut)
def order_payment(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.scalars(select(Order).where(Order.id == order_id, Order.user_id == user.id)).one_or_none()
    if order is None:
        raise HTTPException(404, "Order not found")
    pay = db.scalars(select(Payment).where(Payment.order_id == order.id)).one_or_none()
    if pay is None:
        raise HTTPException(404, "Payment missing")
    return pay
