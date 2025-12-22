from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.core.utils.mixins import BaseResponseMixin
from .models import Shop
from .serializers import (
    ShopListSerializer, 
    ShopDetailSerializer, 
    ShopCreateUpdateSerializer
)


class ShopListView(BaseResponseMixin, APIView):
    """
    GET /api/shops/
    List all shops with filtering
    Query Params: ?shop_owner=<id>, ?search=<text>
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            queryset = Shop.objects.all()
            
            # Filter by shop_owner
            shop_owner = request.query_params.get('shop_owner')
            if shop_owner:
                queryset = queryset.filter(shop_owner_id=shop_owner)
            
            # Search by name or location
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(shop_name__icontains=search) | Q(shop_location__icontains=search)
                )
            
            queryset = queryset.order_by('-created_at')
            serializer = ShopListSerializer(
                queryset, 
                many=True, 
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Shops retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ShopCreateView(BaseResponseMixin, APIView):
    """
    POST /api/shops/create/
    Create new shop with multiple cover images
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            serializer = ShopCreateUpdateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            shop = serializer.save()
            
            response_serializer = ShopDetailSerializer(
                shop,
                context={'request': request}
            )
            return self.created_response(
                data=response_serializer.data,
                message="Shop created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ShopDetailView(BaseResponseMixin, APIView):
    """
    GET /api/shops/<int:pk>/
    Get single shop details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            shop = get_object_or_404(Shop, pk=pk)
            serializer = ShopDetailSerializer(
                shop,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Shop retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ShopUpdateView(BaseResponseMixin, APIView):
    """
    PUT/PATCH /api/shops/<int:pk>/update/
    Update existing shop with multiple cover images
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def put(self, request, pk):
        try:
            shop = get_object_or_404(Shop, pk=pk)
            serializer = ShopCreateUpdateSerializer(
                shop, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            shop = serializer.save()
            
            response_serializer = ShopDetailSerializer(
                shop,
                context={'request': request}
            )
            return self.updated_response(
                data=response_serializer.data,
                message="Shop updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def patch(self, request, pk):
        """PATCH method also supported"""
        return self.put(request, pk)


class ShopDeleteView(BaseResponseMixin, APIView):
    """
    DELETE /api/shops/<int:pk>/delete/
    Delete shop
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            shop = get_object_or_404(Shop, pk=pk)
            shop.delete()
            
            return self.deleted_response(message="Shop deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class ShopEventsListView(BaseResponseMixin, APIView):
    """
    GET /api/shops/<int:shop_pk>/events/
    List all events this shop is participating in
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, shop_pk):
        try:
            # Import here to avoid circular import
            from apps.shopadmin.models import EventShop
            from apps.shop.serializers import EventShopListSerializer
            
            shop = get_object_or_404(Shop, pk=shop_pk)
            event_shops = shop.event_shops.all()
            serializer = EventShopListSerializer(
                event_shops, 
                many=True,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Shop events retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)