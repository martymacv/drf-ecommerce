# drf-ecommerce
## Самостоятельная работа
Самостоятельно были разработаны модели, ендпоинты, миксины и тесты для отзывов о товаре
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
```
# Модуль
python -m pytest tests/test_sellers -v
```