from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from cart.models import DiscountCode, Order, OrderItem
from product.models import Product
from .cart_module import Cart


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
    
class OrderDetailView(View):
    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        return render(request, 'cart/order_detail.html', {'order': order})


class OrderCreationView(View):
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
    

class ApplyDiscontView(View):
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
