from .models import Product, OrderProduct, Order, Customer


# Класс который будит отвечать за корзину при добавлении в неё и удалении

class CartForAuthenticatedUser:
    def __init__(self, request, product_id=None, action=None):
        self.user = request.user

        if product_id and action:
            self.add_or_delete(product_id, action)

    # Метод который будит возвращать инфо о корзине
    def get_cart_info(self):
        customer, created = Customer.objects.get_or_create(  # Из модели Покупатель получаем или создаём покупателя
            user=self.user
        )
        order, created = Order.objects.get_or_create(customer=customer)  # Из модели Заказа получаем или создаём заказ
        order_products = order.orderproduct_set.all()  # Из заказанных продуктов получаем все

        cart_total_quantity = order.get_cart_total_quantity    # Получаем из заказа обш кол-во продуктов
        cart_total_price = order.get_cart_total_price  # Получаем из заказа обш стоимость закзаа

        return {
            'cart_total_quantity': cart_total_quantity,
            'cart_total_price': cart_total_price,
            'order': order,
            'products': order_products
        }

    def add_or_delete(self, product_id, action):
        order = self.get_cart_info()['order']
        product = Product.objects.get(pk=product_id)
        order_product, created = OrderProduct.objects.get_or_create(order=order, product=product) # Получаем или создаём


        if action == 'add' and product.quantity > 0:
            order_product.quantity += 1  # +1 в корзину
            product.quantity -= 1  # -1 на складе
        else:
            order_product.quantity -= 1
            product.quantity += 1

        product.save()
        order_product.save()

        if order_product.quantity <= 0:  # Если кол-во продукта будит нулю то удалит из корзины
            order_product.delete()

    # Метод для удаления товара после оплаты
    def clear(self):
        order = self.get_cart_info()['order']
        order_products = order.orderproduct_set.all()
        for product in order_products:
            product.delete()
        order.save()


# Функция которая при помощи которой мы будим получать всё из класса
def get_cart_data(request):
    cart = CartForAuthenticatedUser(request)
    cart_info = cart.get_cart_info()

    return {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'cart_total_price': cart_info['cart_total_price'],
        'order': cart_info['order'],
        'products': cart_info['products']
    }






