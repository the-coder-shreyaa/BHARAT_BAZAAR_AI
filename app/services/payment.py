"""
Payment service: Razorpay integration with simulation fallback.
"""
import uuid
from app.config import settings
from app.schemas import CheckoutResponse


def create_checkout(order_id: str, amount: float, currency: str = "INR") -> CheckoutResponse:
    """
    Create a checkout/payment for an order.
    Uses Razorpay if configured, otherwise simulates payment.
    """
    if settings.razorpay_enabled:
        return _razorpay_checkout(order_id, amount, currency)
    else:
        return _simulate_checkout(order_id, amount, currency)


def _razorpay_checkout(order_id: str, amount: float, currency: str) -> CheckoutResponse:
    """Create a Razorpay order for payment."""
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Razorpay expects amount in paise (smallest currency unit)
        amount_paise = int(amount * 100)

        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": currency,
            "receipt": order_id,
            "notes": {
                "merchant": settings.MERCHANT_NAME,
                "order_id": order_id,
            }
        })

        return CheckoutResponse(
            order_id=order_id,
            razorpay_order_id=razorpay_order["id"],
            payment_url=f"https://api.razorpay.com/v1/checkout/embedded?order_id={razorpay_order['id']}&key_id={settings.RAZORPAY_KEY_ID}",
            amount=amount,
            currency=currency,
            status="payment_pending",
            message=f"Razorpay payment order created. Amount: ₹{amount}",
            payment_mode="razorpay",
        )
    except Exception as e:
        return CheckoutResponse(
            order_id=order_id,
            amount=amount,
            currency=currency,
            status="payment_failed",
            message=f"Razorpay payment creation failed: {str(e)}",
            payment_mode="razorpay",
        )


def _simulate_checkout(order_id: str, amount: float, currency: str) -> CheckoutResponse:
    """Simulate payment when Razorpay is not configured."""
    sim_payment_id = f"pay_sim_{uuid.uuid4().hex[:12]}"
    sim_order_id = f"order_sim_{uuid.uuid4().hex[:12]}"

    return CheckoutResponse(
        order_id=order_id,
        razorpay_order_id=sim_order_id,
        payment_url=f"http://localhost:{settings.API_PORT}/payment/simulate/{order_id}",
        amount=amount,
        currency=currency,
        status="payment_pending",
        message=f"[SIMULATION MODE] Payment order created. Amount: ₹{amount}. In production, this would redirect to Razorpay checkout.",
        payment_mode="simulation",
    )


def verify_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify Razorpay payment signature. Returns True if valid."""
    if not settings.razorpay_enabled:
        # In simulation mode, always return True
        return True

    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
        return True
    except Exception:
        return False
