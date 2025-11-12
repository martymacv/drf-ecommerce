# drf-ecommerce
## Самостоятельная работа
Самостоятельно были разработаны модели, ендпоинты и миксины для отзывов о товаре
```
# Модуль
from apps.shop.serializers import (
    ProductReviewSerializer, CreateProductReviewSerializer
)
```
```
# Модуль
from apps.shop.models import Review
```
```
# Модуль
from apps.shop.views import ProductReviewsView
```
```
# Модуль
from apps.seller.utils import (
    SellerCalculateMixin, SellerCheckMixin
)
```