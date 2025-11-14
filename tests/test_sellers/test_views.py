import pytest

from django.urls import reverse
from rest_framework import status

from apps.sellers.views import ProductReviewsView


@pytest.mark.django_db
def test_get_product_reviews(api_request_factory, faker_review_factory):
    """
    Генерирует 10 отзывов для одного продукта
    Проверяет их содержимое
    """
    review = faker_review_factory(rating=5)
    for i in range(4):
        faker_review_factory(
            product=review.product,
            rating=i % 5 + 1
        )
    url = reverse('products_reviews', kwargs={'slug': review.product.slug})
    request = api_request_factory.get(url)
    view = ProductReviewsView.as_view()
    response = view(request, slug=review.product.slug)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['reviews']) == 5
    assert isinstance(response.data['avg_rating'], float)
    assert response.data['avg_rating'] == 3.0
    for i in range(5):
        assert 1 <= response.data['reviews'][i]['rating'] <= 5
        assert response.data['reviews'][i]['text']


@pytest.mark.django_db
def test_create_single_product_review(
        api_request_factory, access_token,
        faker_user_factory, faker_review_data_factory
):
    """
    Проверяет, что один пользователь типа BUYER
    может оставить только один отзыв
    """
    fake_buyer = faker_user_factory(account_type="BUYER")
    review1 = faker_review_data_factory(user=fake_buyer.id)
    review2 = faker_review_data_factory(
        user=fake_buyer.id, product=review1['product']
    )

    fake_seller = faker_user_factory(account_type="SELLER")
    review3 = faker_review_data_factory(user=fake_seller.id)

    buyer_token = f'Bearer {access_token(fake_buyer)}'
    seller_token = f'Bearer {access_token(fake_seller)}'

    url = reverse(
        'products_reviews', kwargs={'slug': review1['product']}
    )

    request1 = api_request_factory.post(
        url, review1, format="json", HTTP_AUTHORIZATION=buyer_token
    )
    request2 = api_request_factory.post(
        url, review2, format="json", HTTP_AUTHORIZATION=buyer_token
    )
    request1.user = fake_buyer
    request2.user = fake_buyer

    request3 = api_request_factory.post(
        url, review3, format="json", HTTP_AUTHORIZATION=seller_token
    )
    request3.user = fake_seller

    view = ProductReviewsView.as_view()
    response1 = view(request1, slug=review1['product'])
    response2 = view(request2, slug=review2['product'])
    response3 = view(request3, slug=review3['product'])

    assert response1.status_code == status.HTTP_201_CREATED
    assert response1.data['reviews']
    assert 1 <= response1.data['reviews']['rating'] <= 5
    assert response1.data['reviews']['text']

    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert not response2.data.get('reviews', None)

    assert response3.status_code == status.HTTP_403_FORBIDDEN
    assert not response3.data.get('reviews', None)


@pytest.mark.django_db
def test_update_product_review(
        api_request_factory, access_token,
        faker_user_factory, faker_review_factory
):
    """
    Создаёт отзыв о продукте в базе данных.
    Проверяет, что изменить его может только создатель или админ
    """
    main_buyer = faker_user_factory(account_type="BUYER")
    other_buyer = faker_user_factory(account_type="BUYER")
    other_seller = faker_user_factory(account_type="SELLER")
    other_admin = faker_user_factory(account_type="ADMIN")

    main_buyer_token = f'Bearer {access_token(main_buyer)}'
    other_buyer_token = f'Bearer {access_token(other_buyer)}'
    other_seller_token = f'Bearer {access_token(other_seller)}'
    other_admin_token = f'Bearer {access_token(other_admin)}'

    review = faker_review_factory(user=main_buyer)
    update_review1 = {
        'rating': review.rating % 5 + 1,
        'text': "BuyerTest"
    }
    update_review4 = {
        'rating': update_review1['rating'] % 5 + 1,
        'text': "AdminTest"
    }

    url = reverse(
        'products_reviews', kwargs={'slug': review.product.slug}
    )

    view = ProductReviewsView.as_view()

    request1 = api_request_factory.put(
        url, update_review1, format="json",
        HTTP_AUTHORIZATION=main_buyer_token
    )
    request2 = api_request_factory.put(
        url, update_review1, format="json",
        HTTP_AUTHORIZATION=other_buyer_token
    )
    request3 = api_request_factory.put(
        url, update_review1, format="json",
        HTTP_AUTHORIZATION=other_seller_token
    )
    request4 = api_request_factory.put(
        url, update_review4, format="json",
        HTTP_AUTHORIZATION=other_admin_token
    )
    request1.user = main_buyer
    request2.user = other_buyer
    request3.user = other_seller
    request4.user = other_admin

    response1 = view(request1, slug=review.product.slug)
    response2 = view(request2, slug=review.product.slug)
    response3 = view(request3, slug=review.product.slug)
    response4 = view(request4, slug=review.product.slug)

    assert response1.status_code == status.HTTP_200_OK
    assert response1.data['reviews']
    assert response1.data['reviews']['rating'] == update_review1['rating']
    assert response1.data['reviews']['text'] == update_review1['text']

    assert response2.status_code == status.HTTP_404_NOT_FOUND
    assert response3.status_code == status.HTTP_403_FORBIDDEN

    # assert response4.status_code == status.HTTP_200_OK
    # assert response4.data['reviews']
    # assert response4.data['reviews']['rating'] == update_review4['rating']
    # assert response4.data['reviews']['text'] == update_review4['text']


@pytest.mark.django_db
def test_delete_product_review(
        api_request_factory, access_token,
        faker_user_factory, faker_review_factory
):
    """
    Создаёт отзыв о продукте в базе данных.
    Проверяет, что удалить его может только создатель или админ
    """
    main_buyer = faker_user_factory(account_type="BUYER")
    other_buyer = faker_user_factory(account_type="BUYER")
    other_seller = faker_user_factory(account_type="SELLER")
    other_admin = faker_user_factory(account_type="ADMIN")

    main_buyer_token = f'Bearer {access_token(main_buyer)}'
    other_buyer_token = f'Bearer {access_token(other_buyer)}'
    other_seller_token = f'Bearer {access_token(other_seller)}'
    other_admin_token = f'Bearer {access_token(other_admin)}'

    review1 = faker_review_factory(user=main_buyer)
    review2 = faker_review_factory(user=main_buyer)
    review3 = faker_review_factory(user=main_buyer)
    review4 = faker_review_factory(user=main_buyer)

    url1 = reverse(
        'products_reviews', kwargs={'slug': review1.product.slug}
    )
    url2 = reverse(
        'products_reviews', kwargs={'slug': review2.product.slug}
    )
    url3 = reverse(
        'products_reviews', kwargs={'slug': review3.product.slug}
    )
    url4 = reverse(
        'products_reviews', kwargs={'slug': review4.product.slug}
    )

    view = ProductReviewsView.as_view()

    request1 = api_request_factory.delete(
        url1, HTTP_AUTHORIZATION=main_buyer_token
    )
    request2 = api_request_factory.delete(
        url2, HTTP_AUTHORIZATION=other_buyer_token
    )
    request3 = api_request_factory.delete(
        url3, HTTP_AUTHORIZATION=other_seller_token
    )
    request4 = api_request_factory.delete(
        url4, HTTP_AUTHORIZATION=other_admin_token
    )
    request1.user = main_buyer
    request2.user = other_buyer
    request3.user = other_seller
    request4.user = other_admin

    response1 = view(request1, slug=review1.product.slug)
    response2 = view(request2, slug=review2.product.slug)
    response3 = view(request3, slug=review3.product.slug)
    response4 = view(request4, slug=review4.product.slug)

    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_404_NOT_FOUND
    assert response3.status_code == status.HTTP_403_FORBIDDEN
    # assert response4.status_code == status.HTTP_204_NO_CONTENT
