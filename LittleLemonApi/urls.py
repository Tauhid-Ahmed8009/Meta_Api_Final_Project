from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter(trailing_slash=False)
router.register(r'groups/manager/users', views.ManagersViewSet)
router.register(r'groups/delivery-crew/users', views.DeliveryViewSet)

router.register(r'orders', views.OrderItemViewSet)

# if delete required then add to path.as_view() and provide dict, otherwise use router.register, for Viewsets
# and ModelViewsets

urlpatterns = [
    path('menu-items', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('api-token-auth/', obtain_auth_token),
    path('groups/manager/users/<str:userId>', views.ManagersDestroyView.as_view()),
    path('groups/delivery-crew/users/<str:userId>', views.DeliveryDestroyView.as_view()),
    path(r'cart/menu-items', views.CartViewSet.as_view({
        'get': 'list',
        'post': 'create',
        'delete': 'destroy'
    })),
    path('orders/<str:orderId>', views.OrderViewSet.as_view({
        'get': 'list',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
     })),
]

urlpatterns += router.urls