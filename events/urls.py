from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EventCategoryViewSet,
    EventDetailPageView,
    EventListPageView,
    EventReviewViewSet,
    EventViewSet,
)

app_name = 'events'

router = DefaultRouter()
router.register('api/events', EventViewSet, basename='events-api')
router.register('api/categories', EventCategoryViewSet, basename='categories-api')
router.register('api/reviews', EventReviewViewSet, basename='reviews-api')

urlpatterns = [
    path('', EventListPageView.as_view(), name='list'),
    path('<slug:slug>/', EventDetailPageView.as_view(), name='detail'),
    path('', include(router.urls)),
]
