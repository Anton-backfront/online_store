from random import randint

from django.shortcuts import render, redirect
from .models import *
from django.views.generic import ListView, DetailView
from .forms import ReviewForms, LoginForm, RegistrationForm, CustomerForm, ShippingForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import CartForAuthenticatedUser, get_cart_data
import stripe
from shop import settings


# Create your views here.


class ProductList(ListView):
    model = Product
    context_object_name = 'categories'
    extra_context = {
        'title': 'TOTEMBO: главная страница'
    }
    template_name = 'store/product_list.html'

    def get_queryset(self):
        categories = Category.objects.filter(parent=None)
        return categories


class CategoryView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/category_page.html'

    paginate_by = 1

    # метод для вывода товаров подкатегории
    def get_queryset(self):
        sort_field = self.request.GET.get('sort')
        type_field = self.request.GET.get('type')  # получем подкатегории

        if type_field:  # Проверяем если пришла в запросе подкатегория
            products = Product.objects.filter(category__slug=type_field)
            return products
        main_category = Category.objects.get(slug=self.kwargs['slug'])  # Получаем глав категорию
        subcategories = main_category.subcategories.all()  # Подкатегорию получаем
        products = Product.objects.filter(category__in=subcategories)  # Получаем продукты подкатегорий

        if sort_field:  # Если в запросе пришёл цвет, цена или размер
            products = products.order_by(sort_field)  # То отсартировываем продукты по однуми из параметров
        return products  # и возвращем

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        main_category = Category.objects.get(slug=self.kwargs['slug'])
        context['category'] = main_category
        context['title'] = f'Категория: {main_category.title}'
        return context


class ProductDetail(DetailView):  # Класс будит искать product_detail.html  авутоматически
    model = Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        product = Product.objects.get(slug=self.kwargs['slug'])
        context['title'] = f'{product.title}'

        products = Product.objects.all()
        data = []
        for i in range(4):
            random_index = randint(0, len(products) - 1)
            p = products[random_index]
            if p not in data:
                data.append(p)
        context['products'] = data

        context['reviews'] = Review.objects.filter(product=product)

        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForms()

        return context


# Функция для сохранения  комментариев
def save_review(request, product_id):
    form = ReviewForms(data=request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.author = request.user
        product = Product.objects.get(pk=product_id)
        review.product = product
        review.save()
    else:
        pass
    return redirect('product_detail', product.slug)


# Функция для страницы Логина и Регистрации
def login_registration(request):
    context = {
        'title': 'Войти или зарегистрироваться',
        'login_form': LoginForm(),
        'register_form': RegistrationForm()
    }

    return render(request, 'store/login_register.html', context)


# Функция для логина
def user_login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, 'Вы вошли в Аккаунт')
        return redirect('product_list')
    else:
        messages.error(request, 'Что то пошло не так')
        return redirect('login_registration')


def user_logout(request):
    logout(request)
    messages.warning(request, 'Уже уходите 😥')
    return redirect('product_list')


# Функция для регистрации
def register(request):
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, 'Регистрация прошла успешно')
        return redirect('product_list')
    else:
        for field in form.errors:
            messages.error(request, form.errors[field].as_text())

    return redirect('login_registration')


# Функция для добавления в Избранное
def save_favourite_product(request, product_slug):
    user = request.user if request.user.is_authenticated else None
    product = Product.objects.get(slug=product_slug)
    favourite_products = FavouriteProducts.objects.filter(user=user)
    if user:
        if product in [i.product for i in favourite_products]:
            fav_product = FavouriteProducts.objects.get(user=user, product=product)
            fav_product.delete()
        else:
            FavouriteProducts.objects.create(user=user, product=product)
    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


# Класс для страницы Избранного
class FavouriteProductsView(LoginRequiredMixin, ListView):
    model = FavouriteProducts
    context_object_name = 'products'
    template_name = 'store/favourite_products.html'
    login_url = 'login_registration'

    def get_queryset(self):
        user = self.request.user
        favs = FavouriteProducts.objects.filter(user=user)
        products = [i.product for i in favs]
        return products


# ---------------------------------------------------------------
# Функция для страницы Корзины
def cart(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'products': cart_info['products']
    }

    return render(request, 'store/cart.html', context)


def to_cart(request, product_id, action):
    if request.user.is_authenticated:
        user_cart = CartForAuthenticatedUser(request, product_id, action)
        return redirect('cart')
    else:
        messages.error(request, 'Авторизуйтесь что бы совершить покупку')
        return redirect('login_registration')


# ----------------------------------------------------------------------------------------

# Фунуция для страницы оформления заказа
def checkout(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'products': cart_info['products'],
        'title': 'Оформление заказа',
        'customer_form': CustomerForm(),
        'shipping_form': ShippingForm()

    }

    return render(request, 'store/checkout.html', context)


# Функция для оформления заказа
def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        user_cart = CartForAuthenticatedUser(request)
        cart_info = user_cart.get_cart_info()

        total_price = cart_info['cart_total_price']
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Товара сайта TOTEMBO'
                    },
                    'unit_amount': int(total_price * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('checkout'))
        )
        return redirect(session.url, 303)


#  Написать вьюшку страницы успешной оплаты

def successPayment(request):
    user_cart = CartForAuthenticatedUser(request)
    user_cart.clear()
    messages.success(request, 'Оплата прошла успешно')
    return redirect('product_list')


# Функция для кнопки очищения корзины
def clear_cart(request):
    user_cart = CartForAuthenticatedUser(request)
    order = user_cart.get_cart_info()['order']
    order_products = order.orderproduct_set.all()
    for order_product in order_products:
        quantity = order_product.quantity
        product = order_product.product
        order_product.delete()
        product.quantity += quantity
        product.save()
    return redirect('cart')






