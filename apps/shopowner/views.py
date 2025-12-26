"""
Shop Owner Views - Participation Request Management
File: apps/shopowner/views.py
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.utils.mixins import BaseResponseMixin
from apps.shopadmin.models import EventShopParticipant, EventShop, Event
from apps.shopadmin.serializers import ParticipantListSerializer, ParticipantCreateSerializer
from apps.shop.models import Shop
from apps.shop.serializers import EventShopListSerializer, EventShopCreateSerializer




# ==================== EVENT SHOP MANAGEMENT ====================

class EventShopsListView(BaseResponseMixin, APIView):
    """List all shops in an event"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_pk):
        try:
            event = get_object_or_404(Event, pk=event_pk)
            event_shops = event.event_shops.all()
            serializer = EventShopListSerializer(event_shops, many=True, context={'request': request})
            
            return self.success_response(
                data=serializer.data,
                message="Event shops retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class EventShopCreateView(BaseResponseMixin, APIView):
    """Add shop to event"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = EventShopCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Status will default to 'pending' in model
            event_shop = serializer.save()
            
            response_serializer = EventShopListSerializer(event_shop)
            return self.created_response(
                data=response_serializer.data,
                message="Shop request sent. Waiting for event admin approval"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class EventShopDeleteView(BaseResponseMixin, APIView):
    """Remove shop from event"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            event_shop = get_object_or_404(EventShop, pk=pk)
            event_shop.delete()
            
            return self.deleted_response(message="Shop removed from event successfully")
        except Exception as exc:
            return self.handle_exception(exc)

class ShopRequestListView(BaseResponseMixin, APIView):
    """List pending shop requests for an event (admin only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_pk):
        try:
            event = get_object_or_404(Event, pk=event_pk)
            # Check if user is event admin
            if event.shop_admin != request.user:
                return self.error_response(message="Not authorized")
            
            event_shops = event.event_shops.filter(status='pending')
            serializer = EventShopListSerializer(event_shops, many=True,  context={'request': request})
            
            return self.success_response(
                data=serializer.data,
                message="Pending shop requests retrieved"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ShopRequestApproveView(BaseResponseMixin, APIView):
    """Admin accepts shop request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            event_shop = get_object_or_404(EventShop, pk=pk)
            
            # Check if user is event admin
            if event_shop.event.shop_admin != request.user:
                return self.error_response(message="Not authorized")
            
            event_shop.status = 'accepted'
            event_shop.save()
            
            serializer = EventShopListSerializer(event_shop)
            return self.success_response(
                data=serializer.data,
                message="Shop request approved"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ShopRequestRejectView(BaseResponseMixin, APIView):
    """Admin rejects shop request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            event_shop = get_object_or_404(EventShop, pk=pk)
            
            # Check if user is event admin
            if event_shop.event.shop_admin != request.user:
                return self.error_response(message="Not authorized")
            
            event_shop.status = 'rejected'
            event_shop.save()
            
            return self.success_response(
                message="Shop request rejected"
            )
        except Exception as exc:
            return self.handle_exception(exc)

class ParticipantRequestCreateView(BaseResponseMixin, APIView):
    """
    POST /api/shopowner/participation-requests/create/
    Shop owner creates participation request to join event
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = ParticipantCreateSerializer(
                data=request.data,
                context={'request': request}  # Pass request in context
            )
            serializer.is_valid(raise_exception=True)
            participant = serializer.save()
            
            response_serializer = ParticipantListSerializer(participant)
            return self.created_response(
                data=response_serializer.data,
                message="Participation request created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyParticipationListView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-participations/
    List all participation requests for current shop owner
    Query Params: ?shop_id=<id>, ?status=pending|accepted|rejected
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get shop_id from query params or user's shops
            shop_id = request.query_params.get('shop_id')
            
            if shop_id:
                queryset = EventShopParticipant.objects.filter(
                    event_shop__shop_id=shop_id
                )
            else:
                # Get all participations for shops owned by current user
                queryset = EventShopParticipant.objects.filter(
                    event_shop__shop__shop_owner=request.user
                )
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter in ('accepted', 'rejected', 'pending'):
                queryset = queryset.filter(status=status_filter)
            
            queryset = queryset.order_by('-created_at')
            serializer = ParticipantListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Participations retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyParticipationDetailView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-participations/<int:pk>/
    Get details of a specific participation request
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            participant = get_object_or_404(
                EventShopParticipant,
                pk=pk,
                event_shop__shop__shop_owner=request.user
            )
            serializer = ParticipantListSerializer(participant)
            
            return self.success_response(
                data=serializer.data,
                message="Participation retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyParticipationDeleteView(BaseResponseMixin, APIView):
    """
    DELETE /api/shopowner/my-participations/<int:pk>/cancel/
    Cancel/delete participation request
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            participant = get_object_or_404(
                EventShopParticipant,
                pk=pk,
                event_shop__shop__shop_owner=request.user
            )
            participant.delete()
            
            return self.deleted_response(
                message="Participation request cancelled successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyShopEventsView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-shop-events/
    List all events my shops are participating in
    Query Params: ?event_status=upcoming|ongoing|completed
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            from apps.shop.serializers import EventShopListSerializer
            
            # Get all event-shops for shops owned by current user
            queryset = EventShop.objects.filter(
                shop__shop_owner=request.user
            )
            
            # Filter by event status
            event_status = request.query_params.get('event_status')
            if event_status:
                from datetime import date
                today = date.today()
                
                if event_status == 'upcoming':
                    queryset = queryset.filter(event__from_date__gt=today)
                elif event_status == 'ongoing':
                    queryset = queryset.filter(
                        event__from_date__lte=today,
                        event__to_date__gte=today
                    )
                elif event_status == 'completed':
                    queryset = queryset.filter(event__to_date__lt=today)
            
            queryset = queryset.order_by('-event__from_date')
            serializer = EventShopListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Shop events retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)