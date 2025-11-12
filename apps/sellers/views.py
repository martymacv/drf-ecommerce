from django.db.models import Avg

from drf_spectacular.utils import extend_schema, OpenApiResponse
from requests import delete
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.accounts.models import User
from apps.common.utils import set_dict_attr
from apps.profiles.models import Order, OrderItem
from apps.sellers.models import Seller
from apps.sellers.utils import SellerCalculateMixin, SellerCheckMixin
from apps.shop.models import Category, Product, Review
from apps.sellers.serializers import SellerSerializer
from apps.shop.serializers import (
    CreateProductReviewSerializer, ProductSerializer, CreateProductSerializer,
    OrderSerializer, CheckItemOrderSerializer,
    ProductReviewSerializer
)


tags = ["Sellers"]


class SellersView(APIView):
    serializer_class = SellerSerializer

    @extend_schema(
        summary="Apply to become a seller",
        description=(
            "This endpoint allows a buyer to apply to become a seller"
        ),
        tags=tags
    )
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(
            data=request.data, partial=False
        )
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(
                user=user, defaults=data
            )
            user.account_type = "SELLER"
            user.save()
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=201)
        return Response(data=serializer.errors, status=400)


class SellerProductsView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description=(
            "This endpoint returns all products from a seller\n"
            "Products can be filtered by name, sizes or colors"
        ),
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(
            user=request.user, is_approved=False
        )
        if not seller:
            return Response(
                data={
                    "message": "Access is denied"
                }, status=403
            )
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(
            data=serializer.data, status=200
        )

    @extend_schema(
        summary="Create a product",
        description="""
            This endpoint allows a seller to create a product.
        """,
        tags=tags,
        request=CreateProductSerializer,
        responses=CreateProductSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(
            user=request.user, is_approved=False
        )
        if not seller:
            return Response(data={"message": "Access is denied"}, status=403)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(data={"message": "Category does not exist!"}, status=404)
            data['category'] = category
            data['seller'] = seller
            new_prod = Product.objects.create(**data)
            serializer = self.serializer_class(new_prod)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class SellerProductView(APIView):
    serializer_class = CreateProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product
    
    @extend_schema(
        summary="Seller Products Update",
        description=(
            "This endpoint updates a seller product"
        ),
        tags=tags
    )
    def put(self, request, *args, **kwargs):
        product = self.get_object(kwargs["slug"])
        if not product:
            return Response(
                data={
                    "message": "Product does not exist!"
                }, status=404
            )
        elif product.seller != request.user.seller:
            return Response(
                data={
                    "message": "Access is denied"
                }, status=403
            )
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pip("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(
                    data={
                        "message": "Category does not exist!"
                    }, status=404
                )
            data["category"] = category
            if data["price_current"] != product.price_current:
                data["price_old"] = product.price_current
            product = set_dict_attr(product, data)
            product.save()
            serializer = ProductSerializer(product)
            return Response(
                data=serializer.data, status=200
            )
        return Response(
            data=serializer.errors, status=400
        )
    
    @extend_schema(
        summary="Seller Products Delete",
        description=(
            "This endpoint allows a seller to delete a product"
        ),
        tags=tags
    )
    def delete(self, request, *args, **kwargs):
        product = self.get_object(kwargs["slug"])
        if not product:
            return Response(
                data={
                    "message": "Product does not exists!"
                }, status=404
            )
        elif product.seller != request.user.seller:
            return Response(
                data={
                    "message": "Access is denied"
                }, status=403
            )
        product.delete()
        return Response(
            data={
                "message": "Product deleted successfully"
            }, status=200
        )


class SellerOrdersView(APIView):
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id="seller_orders_view",
        summary="Seller Orders Fetch",
        description=(
            "This endpoint returns all orders for a particular seller"
        ),
        tags=tags
    )
    def get(self, request):
        seller = request.user.seller
        orders = (
            Order.objects
            .filter(orderitems__product__seller=seller)
            .order_by("-created_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(
            data=serializer.data, status=200
        )


class SellerOrderItemsView(APIView):
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id="seller_order_items_view",
        summary="Seller Items Order Fetch",
        description=(
            "This endpoint returns all items order for a particular seller"
        ),
        tags=tags
    )
    def get(self, request, **kwargs):
        seller = request.user.seller
        order = Order.objects.get_or_none(tx_ref(kwargs["tx_ref"]))
        if not order:
            return Response(
                data={
                    "message": "Order does not exist!"
                }, status=404
            )
        order_items = (
            OrderItem.objects
            .filter(order=order, product__seller=seller)
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(
            data=serializer.data, status=200
        )


class ProductReviewsView(
        SellerCalculateMixin, SellerCheckMixin, APIView
):
    """
    Представление ендпоинтов для отзывов
    """
    def get_serializer_class(self, method):
        """
        Возвращает соответствующий сериализатор для метода
        """
        serializer_map = {
            'GET': ProductReviewSerializer,          # Для списка отзывов
            'POST': CreateProductReviewSerializer,   # Для создания
            'PUT': CreateProductReviewSerializer,    # Для обновления
        }
        return serializer_map.get(method, ProductReviewSerializer)

    @extend_schema(
        summary="Product Review Fetch",
        description=(
            "В этом ендпоинте реализована возможность "
            "просматривать отзывы о продукте"
        ),
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        """
        Запрашивает все отзывы по продукту
        """
        serializer_class = self.get_serializer_class(request.method)
        product = self.check_product(
            Product.objects.get_or_none(slug=kwargs["slug"])
        )
        reviews = (
            Review.objects
            .filter(product=product)
            .order_by("-created_at")
        )
        serializer = serializer_class(reviews, many=True)
        avg_product_rating = self.get_average_product_rating(
            product=product, model=Review
        )
        return Response(
            data={
                "reviews": serializer.data,
                **avg_product_rating
            },
        )

    @extend_schema(
        summary="Create new Product Review",
        description=(
            "Метод для создания отзыва о продукте. "
            "Один пользователь может оставить только один отзыв"
        ),
        tags=tags
    )
    def post(self, request, *args, **kwargs):
        """
        Создаёт новый отзыв, если пользователь BUYER
        и если пользователь не оставлял отзыва о продукте
        """
        serializer_class = self.get_serializer_class(request.method)
        user = self.check_user(request.user, "BUYER")
        product = self.check_product(
            Product.objects.get_or_none(slug=kwargs["slug"])
        )
        self.check_review_by_unique(
            Review.objects.get_or_none(user=user, product=product)
        )
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['user'] = user
            data['product'] = product
            new_review = Review.objects.create(**data)
            serializer = serializer_class(new_review)
            avg_product_rating = self.get_average_product_rating(
                product=product, model=Review
            )
            return Response(
                data={
                    "reviews": serializer.data,
                    **avg_product_rating
                }, status=201
            )
        return Response(
            data=serializer.errors, status=404
        )

    @extend_schema(
        summary="Update Product Review",
        description=(
            "В этом ендпоинте реализована возможность "
            "изменить свой отзыв о продукте"
        ),
        tags=tags
    )
    def put(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class(request.method)
        user = self.check_user(request.user, "BUYER")
        product = self.check_product(
            Product.objects.get_or_none(slug=kwargs["slug"])
        )
        review = self.check_review(
            Review.objects.get_or_none(user=user, product=product)
        )
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            review.rating = data['rating']
            review.text = data['text']
            review.save()
            avg_product_rating = self.get_average_product_rating(
                product=product, model=Review
            )
            return Response(
                data={
                    "reviews": serializer.data,
                    **avg_product_rating
                }, status=200
            )
        return Response(
            data=serializer.errors, status=404
        )

    @extend_schema(
        summary="Delete Product Review",
        description=(
            "В этом ендпоинте реализована возможность "
            "удалять собственные отзывы о продукте"
        ),
        tags=tags
    )
    def delete(self, request, *args, **kwargs):
        """
        Удаляется отзыв пользователя о продукте
        """
        user = self.check_user(request.user, "BUYER")
        product = self.check_product(
            Product.objects.get_or_none(slug=kwargs["slug"])
        )
        review = self.check_review(
            Review.objects.get_or_none(user=user, product=product)
        )
        review.delete()
        return Response(
            data={
                "message": "Your review has been deleted!"
            }, status=status.HTTP_204_NO_CONTENT
        )
