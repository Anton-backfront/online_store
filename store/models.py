from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


# Create your models here.

class Category(models.Model):
    title = models.CharField(max_length=150, verbose_name='Наименование Категории')
    image = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name='Изображение')
    slug = models.SlugField(unique=True, null=True)  # заменяет обращение по pk или id
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               null=True, blank=True,
                               verbose_name='Категория',
                               related_name='subcategories')

    # Умная ссылка для категорий
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    #
    #  Метод для получения картинки категории
    def get_image(self):
        if self.image:
            return self.image.url
        else:
            return 'https://avatars.mds.yandex.net/get-mpic/4614963/img_id1492585197771787400.jpeg/600x800'

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'Категория: pk={self.pk}, title={self.title}'

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Product(models.Model):
    title = models.CharField(max_length=150, verbose_name='Наименование продукта')
    price = models.FloatField(verbose_name='Цена')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    description = models.TextField(default='Здесь скоро будит описание', verbose_name='Описание товара')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='products')
    slug = models.SlugField(unique=True, null=True)
    size = models.IntegerField(default=30, verbose_name='Размер в мм')
    color = models.CharField(max_length=40, default='Серебро', verbose_name='Цвет/Материал')

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    # Метод для получения первого фото продукта
    def get_first_photo(self):
        if self.images:
            try:
                return self.images.first().image.url
            except:
                return 'https://avatars.mds.yandex.net/get-mpic/4614963/img_id1492585197771787400.jpeg/600x800'
        else:
            return 'https://avatars.mds.yandex.net/get-mpic/4614963/img_id1492585197771787400.jpeg/600x800'

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'Товар: pk={self.pk}, title={self.title}, price={self.price}'

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class Gallery(models.Model):
    image = models.ImageField(upload_to='products/', verbose_name='Изображения')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения товаров'


class Review(models.Model):
    text = models.TextField(verbose_name='Текст отзыв')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.author.username

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


#  Модель для избранных товаров
class FavouriteProducts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')

    def __str__(self):
        return self.product.title

    class Meta:
        verbose_name = 'Избранный товар'
        verbose_name_plural = 'Избранные товары'


# ----------------------------------------------------------------------------------------------------------

# Модель Покупателя
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Покупатель')
    first_name = models.CharField(max_length=255, verbose_name='Имя покупателя', default='')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия покупателя', default='')


    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


# Модель Заказа
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Покупатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    shipping = models.BooleanField(default=True, verbose_name='Доставка')

    def __str__(self):
        return str(self.pk) + ' '

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    # Здесьбудут методы для подсчёте кол-ва и общ стоимости продуктов
    @property
    def get_cart_total_price(self):
        order_products = self.orderproduct_set.all()
        total_price = sum([product.get_total_price for product in order_products])  # Получим список стоимости каждого продукта в кол-во
        return total_price

    @property
    def get_cart_total_quantity(self):
        order_products = self.orderproduct_set.all()
        total_quantity = sum([product.quantity for product in order_products])  # Получим список  кол-во заказ продуктов
        return total_quantity



#  Продукты в Заказе
class OrderProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='Продукт')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, verbose_name='Заказ')
    quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name='Количество')
    addet_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    # Данный декоратор позваляет вызвать метод в другом классе
    @property
    def get_total_price(self):  # Метод для подсчёта товара на какую сумму определённый товар в кол-ве
        total_price = self.product.price * self.quantity
        return total_price



# Модель Адреса Доставки
class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'Адресс Доставки'
        verbose_name_plural = 'Адресса Доставок'

















