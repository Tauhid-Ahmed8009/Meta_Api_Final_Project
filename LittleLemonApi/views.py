from django.db import transaction
from django.db.models import Sum
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, api_view, action
from django.contrib.auth.models import User, Group
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .serializers import MenuItemSerializer, UserSerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from .models import MenuItem, Cart, OrderItem, Order
from .permissions import AllowManagerCrudReadAll, AllowManagerOnly, AllowCustomerOnly, AllowDeliveryCrewOnly
from datetime import date

@permission_classes([AllowManagerCrudReadAll | IsAdminUser])
class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


@permission_classes([AllowManagerCrudReadAll | IsAdminUser])
class SingleMenuItemView(generics.RetrieveUpdateAPIView, generics.DestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


@permission_classes([AllowManagerOnly | IsAdminUser])
class ManagersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post']

    def list(self, request, *args, **kwargs):
        manager_group = Group.objects.get(name='Manager')
        manager_users = User.objects.filter(groups=manager_group)

        serializer = self.serializer_class(manager_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        username = self.request.data['username']
        manager_group = Group.objects.get(name='Manager')

        try:
            user = User.objects.get(username=username)
            user.groups.add(manager_group)
            return Response({'message': 'created'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([AllowManagerOnly | IsAdminUser])
class ManagersDestroyView(APIView):

    def delete(self, request, *args, **kwargs):
        username = kwargs['userId']
        manager_group = Group.objects.get(name='Manager')

        try:
            user = User.objects.get(username=username)
            user.groups.remove(manager_group)
            return Response({'message': 'Ok'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'Not found'}, status.HTTP_404_NOT_FOUND)


@permission_classes([AllowManagerOnly | IsAdminUser])
class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post']

    def list(self, request, *args, **kwargs):
        manager_group = Group.objects.get(name='Delivery crew')
        manager_users = User.objects.filter(groups=manager_group)

        serializer = self.serializer_class(manager_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        username = self.request.data['username']
        delivery_crew_group = Group.objects.get(name='Delivery crew')

        try:
            user = User.objects.get(username=username)
            user.groups.add(delivery_crew_group)
            return Response({'message': 'created'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([AllowManagerOnly | IsAdminUser])
class DeliveryDestroyView(APIView):

    def delete(self, request, *args, **kwargs):
        username = kwargs['userId']
        delivery_crew_group = Group.objects.get(name='Delivery crew')

        try:
            user = User.objects.get(username=username)
            user.groups.remove(delivery_crew_group)
            return Response({'message': 'Ok'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'Not found'}, status.HTTP_404_NOT_FOUND)


@permission_classes([AllowCustomerOnly])
class CartViewSet(viewsets.ViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def list(self, request):
        queryset = Cart.objects.filter(user=request.user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        cart_data = request.data.copy()
        cart_data['user'] = request.user.id
        serializer = self.serializer_class(data=cart_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        queryset = Cart.objects.filter(user=request.user)
        for obj in queryset:
            obj.delete()
        return Response({'message': 'Ok'}, status=status.HTTP_200_OK)


class OrderItemViewSet(viewsets.ViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def list(self, request):
        # Create instances of the permission classes
        customer_permission = AllowCustomerOnly()
        manager_permission = AllowManagerOnly()
        # customers list operation:
        if customer_permission.has_permission(request, self):
            queryset = self.queryset.filter(order=request.user)
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    #     managers list operation:
        if manager_permission.has_permission(request, self):
            queryset = Order.objects.all()
            serializer = OrderSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        customer_permission = AllowCustomerOnly()
        if customer_permission.has_permission(request, self):
            carts = Cart.objects.filter(user=request.user)
            if len(carts) > 0:
                # CREATES ORDER OBJECT:
                total = carts.aggregate(total=Sum('price')).get('total')
                Order.objects.create(user=request.user, total=total, date=date.today())
                # CREATES ORDER ITEMS:
                # Loop through the filtered Cart objects and create corresponding OrderItem objects
                with transaction.atomic():
                    for cart_item in carts:
                        # You can access the related user and menu item from the Cart object
                        user = cart_item.user
                        menu_item = cart_item.menuitem
                        quantity = cart_item.quantity
                        unit_price = cart_item.unit_price
                        price = cart_item.price
                        try:
                            # Create the OrderItem object using the retrieved values
                            OrderItem.objects.create(
                                order=user,
                                menuitem=menu_item,
                                quantity=quantity,
                                unit_price=unit_price,
                                price=price
                            )
                        except Exception as e:
                            return Response(status=status.HTTP_400_BAD_REQUEST)

                # delete carts:
                carts.delete()
                return Response({'message': 'Created'}, status=status.HTTP_201_CREATED)
            else:
                return Response(status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status.HTTP_400_BAD_REQUEST)
