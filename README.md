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
from apps.sellers.views import ProductReviewsView
```
```
# Модуль
from apps.sellers.utils import (
    SellerCalculateMixin, SellerCheckMixin
)
```