from email.policy import default
from apps.accounts.models import User
from apps.shop.models import Product, Review
from rest_framework.exceptions import (
    NotFound, PermissionDenied, ValidationError
)
from rest_framework import status
from django.db.models import Model, Avg


class SellerCheckMixin:
    """Миксин с проверками данных"""
    def check_product(self, product: Product) -> Product:
        """Проверяется наличие товара"""
        if product is None:
            raise NotFound("Product not found")
        return product

    def check_user(
            self, user: User, account_type: str = "SELLER"
    ) -> User:
        """
        Проверяется тип аккаунта пользователя,
        если пользователь не проходит проверку,
        то ему возвращается сообщение, что он
        не может совершать никаких действий
        """
        if user.account_type != account_type:
            raise PermissionDenied(
                f"You are not a {account_type}, "
                "so you can't leave any actions"
            )
        return user

    def check_review(self, review: Review) -> Review:
        """Проверяется существование отзыва"""
        if review is None:
            raise NotFound("Reiview not found")
        return review

    def check_review_by_unique(self, review: Review) -> Review:
        """
        Проверяется уникальность ключа:
        пользователь - продукт - отзыв
        """
        if review is not None:
            raise ValidationError(
                detail={
                    "message": "Вы уже оставили отзыв об этом продукте",
                },
                code=status.HTTP_400_BAD_REQUEST
            )
        return review


class SellerCalculateMixin:
    """Сборник методов рассчёта"""
    def get_average_product_rating(
            self, product: Product, model: type[Review]
    ) -> dict:
        """
        Пересчитывается средняя оценка продукта
        """
        return (
            model.objects
            .filter(product=product)
            .aggregate(
                avg_rating=Avg('rating', default=0)
            )
        )
