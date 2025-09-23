from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from account.models import Address
from cart.models import DiscountCode, Order, OrderItem
from product.models import Product
from .cart_module import Cart
from django.conf import settings
import requests
import json

import stripe
from django.urls import reverse
from django.http import JsonResponse

class CartDetailView(View):
    def get(self, request):
        cart = Cart(request)
        return render(request, 'cart/cart_detail.html', {'cart': cart})

class CartAddView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        size = request.POST.get('size', 'empty')
        color = request.POST.get('color', 'empty')
        quantity = request.POST.get('quantity')
        
        cart = Cart(request)
        cart.add(product, quantity, color, size)
        return redirect('cart:cart_detail')
    
class CartDeleteView(View):
    def get(self, request, id):
        cart = Cart(request)
        cart.delete(id)
        print(id)
        return redirect('cart:cart_detail')
    
class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        return render(request, 'cart/order_detail.html', {'order': order})


class OrderCreationView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart(request)
        order = Order.objects.create(user=request.user, total_price=cart.total())
        for item in cart:
            OrderItem.objects.create(order=order, 
                                     product=item['product'], 
                                     color=item['color'], 
                                     size=item['size'], 
                                     quantity=item['quantity'], 
                                     price=item['price'])
        cart.remove_cart()
        return redirect('cart:order_detail', order.id)
    

class ApplyDiscontView(LoginRequiredMixin, View):
    def post(self, request, pk):
        code = request.POST.get('discount_code')
        order = get_object_or_404(Order, id=pk)
        discount_code = get_object_or_404(DiscountCode, name=code)
        if discount_code.quantity == 0:
            return redirect('cart:order_detail', order.id)
        order.total_price -= order.total_price * discount_code.discount / 100
        order.save()
        discount_code.quantity -= 1
        discount_code.save()
        return redirect('cart:order_detail', order.id)



class SendRequestView(View):
    def post(self, request, pk):
        # 1) بارگیری سفارش و آدرس
        order = get_object_or_404(Order, id=pk, user=request.user)
        address_id = request.POST.get("address")
        address_obj = get_object_or_404(Address, id=address_id, user=request.user)

        # 2) ذخیره آدرس در سفارش (بعد از تغییر مدل به TextField)
        order.address = f"{address_obj.address} - {address_obj.phone} - {address_obj.email}"
        order.save()

        # 3) مقداردهی Stripe با secret key
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # 4) ساخت آدرس‌های بازگشت (success / cancel)
            success_url = request.build_absolute_uri(
                reverse('cart:verify_request')
            ) + "?session_id={CHECKOUT_SESSION_ID}"  # Stripe جایگزاری می‌کند
            cancel_url = request.build_absolute_uri(
                reverse('cart:order_detail', args=[order.id])
            )

            # 5) ساخت یک Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'jpy',
                        'product_data': {'name': f'Order #{order.id}'},
                        'unit_amount': int(order.total_price),  # JPY: 1 = 1円
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'order_id': str(order.id), 'user_id': str(request.user.id)}
            )

            # 6) ریدایرکت به صفحه پرداخت Stripe
            return redirect(session.url, code=303)

        except stripe.error.StripeError as e:
            # در صورت خطای Stripe یک JSON با خطا برگردان یا ریدایرکت به صفحه خطا
            return JsonResponse({'status': False, 'error': str(e)}, status=500)


class VerifyView(View):
    def get(self, request):
        # 1) گرفتن session_id از URL
        session_id = request.GET.get("session_id")
        if not session_id:
            return JsonResponse({"status": False, "error": "Missing session_id"}, status=400)

        # 2) مقداردهی Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # 3) بازیابی session از Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            print("Stripe payment_status:", session.payment_status)

            # 4) گرفتن order از metadata
            order_id = session.metadata.get("order_id")
            order = get_object_or_404(Order, id=order_id, user=request.user)

            # 5) تایید پرداخت
            if session.payment_status == "paid":
                order.is_paid = True
                order.save()
                return JsonResponse({"status": True, "session_id": session.id})
            else:
                print(session.payment_status)
                return JsonResponse({"status": False, "payment_status": session.payment_status})

        except stripe.error.StripeError as e:
            return JsonResponse({"status": False, "error": str(e)}, status=500)