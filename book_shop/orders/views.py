from django.shortcuts import render, aget_object_or_404, redirect
from books.models import Book

from orders.models import OrderItem
from orders.cart.cart import Cart
from orders.forms import OrderCreateForm

# Create your views here.


async def cart_add(request, pk):
    """Add ``quantity`` of the given book to the session cart, then redirect.

    ``quantity`` comes from the POST body and defaults to 1; a
    non-numeric value falls back to 1 instead of raising a 500 error.
    Non-POST requests just redirect without changing the cart.
    """
    cart = await Cart.async_create(request)
    book = await aget_object_or_404(Book, pk=pk)
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1
        cart.add_item(book, quantity)
    return redirect("payment:cart_detail")


async def cart_detail(request):
    """Render the current session cart with its line items and running total."""
    cart = await Cart.async_create(request)
    items = [item async for item in cart.async_iter()]
    context = {"cart": cart, "items": items, "total_price": cart.get_total()}
    return render(request, "cart/cart_detail.html", context)


async def cart_remove(request, pk):
    """Remove the given book from the session cart, then redirect to the cart."""
    cart = await Cart.async_create(request)
    book = await aget_object_or_404(Book, pk=pk)
    cart.remove(book)
    return redirect("payment:cart_detail")


async def order_create(request):
    """Show the order form (GET) or create the order from the cart (POST).

    Redirects back to the cart if it's empty. On a valid POST, the order
    is linked to the authenticated user (if any) and given their email as
    a default, an ``OrderItem`` is created per cart line, and the cart is
    cleared before showing the success page. Anonymous checkout is still
    supported: ``order.user`` stays ``None`` and only ``order.email`` (from
    the submitted form) is used.
    """
    cart = await Cart.async_create(request)
    user = await request.auser()
    if not cart.cart:
        return redirect("payment:cart_detail")
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = cart.get_total()
            if user.is_authenticated:
                order.user = user
                if not order.email:
                    order.email = user.email
            await order.asave()
            async for item in cart.async_iter():
                await OrderItem.objects.acreate(
                    order=order,
                    book=item["book"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
            await cart.async_clear()
            return render(request, "orders/success.html", {"order": order})
    else:
        defaults = {}
        if user.is_authenticated:
            defaults = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }
        form = OrderCreateForm(initial=defaults)
    context = {"form": form, "cart": cart, "total_price": cart.get_total()}

    return render(request, "orders/order_create.html", context)
