import pytest
from faker import Faker

from django.urls import reverse

from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.shop.models import Review, Product, Category
from apps.sellers.models import Seller


fake = Faker()  # Создаем экземпляр Faker
Faker.seed(42)  # Для воспроизводимости результатов


@pytest.fixture
def api_request_factory():
    """Создаёт фабрику api-реквестов"""
    return APIRequestFactory()


@pytest.fixture
def access_token():
    """
    Создаёт фабрику токенов, чтобы токен всегда был актуальный
    Возвращает Access Token для авторизованных действий
    """
    def create_token(user: User):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    return create_token


@pytest.fixture
def faker_user_factory():
    """Создаёт фейкового пользователя"""
    def create_user(**kwargs):
        defaults = {
            'email': fake.unique.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'password': 'testpass123',  # пароль для тестов
            'avatar': 'avatars/default.jpg',
            # is_staff=fake.boolean(chance_of_getting_true=10),  # 10% шанс быть staff
            'is_active': True,
            'account_type': 'SELLER'
        }
        defaults.update(kwargs)
        user = User.objects.create_user(**defaults)
        return user
    return create_user


@pytest.fixture
def faker_sellers_factory(faker_user_factory):
    """Создаёт фейкового продавца"""
    def create_seller(**kwargs):
        defaults = {
            'business_name': fake.company(),
            'inn_identification_number': fake.random_number(digits=12, fix_len=True),
            'website_url': fake.url(),
            'phone_number': fake.phone_number(),
            'business_description': fake.paragraph(nb_sentences=3),
            'business_address': fake.street_address(),
            'city': fake.city(),
            'postal_code': fake.postcode(),
            'bank_name': fake.company() + ' Bank',
            'bank_bic_number': fake.random_number(digits=9, fix_len=True),
            'bank_account_number': fake.random_number(digits=20, fix_len=True),
            'bank_routing_number': fake.random_number(digits=9, fix_len=True),
            'is_approved': fake.boolean(chance_of_getting_true=80),  # 80% шанс быть approved
        }
        defaults.update(kwargs)

        defaults.setdefault(
            'user', faker_user_factory(account_type="SELLER")
        )

        seller = Seller.objects.create(**defaults)
        return seller
    return create_seller


@pytest.fixture
def faker_category_factory():
    """Создаёт фейковую категорию продукта"""
    def create_category(**kwargs):
        defaults = {
            'name': fake.unique.word().title(),  # Уникальное название с заглавной буквы
            'image': 'category_images/default.jpg',
        }
        defaults.update(kwargs)
        category = Category.objects.create(**defaults)
        return category
    return create_category


@pytest.fixture
def faker_product_factory(faker_sellers_factory, faker_category_factory):
    """Создаёт фейковый продукт"""
    def create_product(**kwargs):
        defaults = {
            'name': fake.unique.catch_phrase(),
            'desc': fake.paragraph(nb_sentences=3),
            'price_old': fake.random_number(digits=3, fix_len=True) + 0.99,
            'price_current': fake.random_number(digits=2, fix_len=True) + 0.99,
            'in_stock': fake.random_int(min=0, max=100),
            'image1': 'product_images/default.jpg',
            'image2': '',
            'image3': '',
        }
        defaults.update(kwargs)

        defaults.setdefault(
            'seller', faker_sellers_factory()
        )
        defaults.setdefault(
            'category', faker_category_factory()
        )

        product = Product.objects.create(**defaults)
        return product
    return create_product


@pytest.fixture
def faker_review_factory(faker_user_factory, faker_product_factory):
    """Создаёт один фейковый отзыв"""
    def create_review(**kwargs):
        defaults = {
            'rating': fake.random_int(min=1, max=5),
            'text': fake.paragraph(nb_sentences=3),
        }
        defaults.update(kwargs)

        defaults.setdefault(
            'product', faker_product_factory()
        )
        defaults.setdefault(
            'user', faker_user_factory(account_type="BUYER")
        )

        review = Review.objects.create(**defaults)
        return review
    return create_review


@pytest.fixture
def faker_review_data_factory(faker_user_factory, faker_product_factory):
    """Генерирует данные для фейкового отзыв"""
    def get_review_data(**kwargs):
        defaults = {
            'rating': fake.random_int(min=1, max=5),
            'text': fake.paragraph(nb_sentences=3),
        }
        defaults.update(kwargs)

        defaults.setdefault(
            'product', faker_product_factory().slug
        )
        defaults.setdefault(
            'user', faker_user_factory(account_type="BUYER").id
        )

        return defaults
    return get_review_data
