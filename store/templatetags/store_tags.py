from django import template
from store.models import Category, FavouriteProducts

register = template.Library()


# Функция для получения категорий у котрых нет родителя
@register.simple_tag()
def get_categories():
    return Category.objects.filter(parent=None)


# Функция для получения под категорий
@register.simple_tag()
def get_subcategories(category):
    return Category.objects.filter(parent=category)


@register.simple_tag()
def get_sorted():
    sorters = [
        {
            'title': 'По цене',
            'sorters': [
                ('price', 'По возрастанию'),
                ('-price', 'По убыванию'),
            ]
        },

        {
            'title': 'По цвету',
            'sorters': [
                ('color', 'От А до Я'),
                ('-color', 'От Я до А'),
            ]
        },

        {
            'title': 'По размеру',
            'sorters': [
                ('size', 'По возрастанию'),
                ('-size', 'По убыванию'),
            ]
        }

    ]
    return sorters


# Функция для получения Избранных товаров по Пользователю
@register.simple_tag()
def get_favourite_products(user):
    fav = FavouriteProducts.objects.filter(user=user)
    products = [i.product for i in fav]
    print(f'Избранные товары Пользователя  {products}')
    return products









