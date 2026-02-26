"""
Shop Owner Views - Participation Request Management
File: apps/shopowner/views.py
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import logging

from apps.core.utils.mixins import BaseResponseMixin
from apps.shopadmin.models import EventShopParticipant, EventShop, Event, EventParticipant
from apps.shopadmin.serializers import (
    ParticipantListSerializer, ParticipantCreateSerializer,
    EventParticipantListSerializer, EventParticipantCreateSerializer, EventParticipantDetailSerializer,
    ShopOwnerEventWithShopsSerializer
)
from apps.shop.models import Shop
from apps.shop.serializers import EventShopListSerializer, EventShopCreateSerializer
from apps.notification.services.notification_service import NotificationService

logger = logging.getLogger(__name__)




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
            response_data = self.success_response(
                data=serializer.data,
                message="Shop request approved"
            )
            
            # Send notification to shop owner (async)
            try:
                shop_owner = event_shop.shop.shop_owner
                shop_name = event_shop.shop.shop_name
                event_name = event_shop.event.name
                NotificationService.send_notification(
                    user_id=shop_owner.id,
                    title="Shop Request Approved",
                    message=f"Your shop '{shop_name}' has been approved to participate in '{event_name}'.",
                    notification_types=['in_app', 'push'],
                    data={
                        "action": "shop_request_approved",
                        "event_shop_id": event_shop.id,
                        "event_id": event_shop.event.id
                    }
                )
            except Exception as notif_exc:
                logger.error(f"Failed to send approval notification: {notif_exc}", exc_info=True)
            
            return response_data
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
            
            response_data = self.success_response(
                message="Shop request rejected"
            )
            
            # Send notification to shop owner (async)
            try:
                shop_owner = event_shop.shop.shop_owner
                shop_name = event_shop.shop.shop_name
                event_name = event_shop.event.name
                NotificationService.send_notification(
                    user_id=shop_owner.id,
                    title="Shop Request Rejected",
                    message=f"Your shop '{shop_name}' request for '{event_name}' has been rejected.",
                    notification_types=['in_app', 'push'],
                    data={
                        "action": "shop_request_rejected",
                        "event_shop_id": event_shop.id,
                        "event_id": event_shop.event.id
                    }
                )
            except Exception as notif_exc:
                logger.error(f"Failed to send rejection notification: {notif_exc}", exc_info=True)
            
            return response_data
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
                context={'request': request} 
            )
            serializer.is_valid(raise_exception=True)
            participant = serializer.save()
            
            response_serializer = ParticipantListSerializer(participant)
            response_data = self.created_response(
                data=response_serializer.data,
                message="Participation request created successfully"
            )
            
            # Send notification to event admin (async)
            try:
                event_admin = participant.event_shop.event.shop_admin
                shop_name = participant.event_shop.shop.shop_name
                NotificationService.send_notification(
                    user_id=event_admin.id,
                    title="New Shop Participation Request",
                    message=f"Shop '{shop_name}' has requested to participate in your event.",
                    notification_types=['in_app', 'push'],
                    data={
                        "action": "shop_participation_request",
                        "participant_id": participant.id,
                        "shop_id": participant.event_shop.shop.id
                    }
                )
            except Exception as notif_exc:
                logger.error(f"Failed to send notification: {notif_exc}", exc_info=True)
            
            return response_data
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
        

class MyShopsListView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-shops/
    List all shops owned by the current user
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            shops = Shop.objects.filter(shop_owner=request.user).order_by('-created_at')
            from apps.shop.serializers import ShopDetailSerializer
            serializer = ShopDetailSerializer(shops, many=True, context={'request': request})
            
            return self.success_response(
                data=serializer.data,
                message="My shops retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== EVENT-LEVEL PARTICIPATION ====================

class EventParticipationRequestCreateView(BaseResponseMixin, APIView):
    """
    POST /api/shopowner/event-participation-requests/create/
    Shopper creates participation request to join event (not specific shop)
    Once approved, shopper can join shops in that event
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = EventParticipantCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            participant = serializer.save()
            
            response_serializer = EventParticipantListSerializer(
                participant,
                context={'request': request}
            )
            response_data = self.created_response(
                data=response_serializer.data,
                message="Event participation request created successfully"
            )
            
            # Send notification to event admin (async)
            try:
                event_admin = participant.event.shop_admin
                shopper_name = request.user.get_full_name() or request.user.username
                event_name = participant.event.name
                NotificationService.send_notification(
                    user_id=event_admin.id,
                    title="New Event Participation Request",
                    message=f"{shopper_name} has requested to participate in '{event_name}'.",
                    notification_types=['in_app', 'push'],
                    data={
                        "action": "event_participation_request",
                        "participant_id": participant.id,
                        "event_id": participant.event.id,
                        "shopper_id": request.user.id
                    }
                )
            except Exception as notif_exc:
                logger.error(f"Failed to send participation notification: {notif_exc}", exc_info=True)
            
            return response_data
        except Exception as exc:
            return self.handle_exception(exc)


class MyEventParticipationListView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-event-participations/
    List all event participation requests for current shopper
    Query Params: ?status=pending|accepted|rejected, ?event_id=<id>
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all event participations for current user
            queryset = EventParticipant.objects.filter(
                shopper=request.user
            )
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter in ('accepted', 'rejected', 'pending'):
                queryset = queryset.filter(status=status_filter)
            
            # Filter by event
            event_id = request.query_params.get('event_id')
            if event_id:
                queryset = queryset.filter(event_id=event_id)
            
            queryset = queryset.order_by('-created_at')
            serializer = EventParticipantListSerializer(
                queryset,
                many=True,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Event participations retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyEventParticipationDetailView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-event-participations/<int:pk>/
    Get details of a specific event participation request
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            participant = get_object_or_404(
                EventParticipant,
                pk=pk,
                shopper=request.user
            )
            serializer = EventParticipantDetailSerializer(
                participant,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Event participation retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyEventParticipationDeleteView(BaseResponseMixin, APIView):
    """
    DELETE /api/shopowner/my-event-participations/<int:pk>/cancel/
    Cancel/delete event participation request
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            participant = get_object_or_404(
                EventParticipant,
                pk=pk,
                shopper=request.user
            )
            # Only allow deletion if pending
            if participant.status != 'pending':
                return self.error_response(
                    message=f"Cannot cancel a {participant.status} participation request"
                )
            
            participant.delete()
            
            return self.deleted_response(
                message="Event participation request cancelled successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class EventParticipationApproveView(BaseResponseMixin, APIView):
    """
    POST /api/shopowner/event-participations/<int:pk>/approve/
    Event admin approves event participation request
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            participant = get_object_or_404(EventParticipant, pk=pk)
            
            # Check if user is event admin
            # if participant.event.shop_admin != request.user:
            #     return self.error_response(message="Not authorized")
            
            if participant.status != 'pending':
                return self.error_response(
                    message=f"Cannot approve a {participant.status} participation request"
                )
            
            participant.status = 'accepted'
            participant.save()
            
            serializer = EventParticipantListSerializer(
                participant,
                context={'request': request}
            )
            response_data = self.success_response(
                data=serializer.data,
                message="Event participation approved"
            )
            
            # Send notification to shopper (async)
            try:
                shopper = participant.shopper
                event_name = participant.event.name
                NotificationService.send_notification(
                    user_id=shopper.id,
                    title="Participation Approved",
                    message=f"Your request to participate in '{event_name}' has been approved!",
                    notification_types=['in_app', 'push'],
                    data={
                        "action": "participation_approved",
                        "participant_id": participant.id,
                        "event_id": participant.event.id
                    }
                )
            except Exception as notif_exc:
                logger.error(f"Failed to send approval notification: {notif_exc}", exc_info=True)
            
            return response_data
        except Exception as exc:
            return self.handle_exception(exc)


class EventParticipationRejectView(BaseResponseMixin, APIView):
    """
    POST /api/shopowner/event-participations/<int:pk>/reject/
    Event admin rejects event participation request
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            participant = get_object_or_404(EventParticipant, pk=pk)
            
            # Check if user is event admin
            # if participant.event.shop_admin != request.user:
            #     return self.error_response(message="Not authorized")
            
            if participant.status != 'pending':
                return self.error_response(
                    message=f"Cannot reject a {participant.status} participation request"
                )
            
            participant.status = 'rejected'
            participant.save()
            
            response_data = self.success_response(
                message="Event participation rejected"
            )
            
            # Send notification to shopper (async)
            try:
                shopper = participant.shopper
                event_name = participant.event.name
                NotificationService.send_notification(
                    user_id=shopper.id,
                    title="Participation Request Rejected",
                    message=f"Your request to participate in '{event_name}' has been rejected.",
                    notification_types=['in_app', 'push'],
                    data={
                        "action": "participation_rejected",
                        "participant_id": participant.id,
                        "event_id": participant.event.id
                    }
                )
            except Exception as notif_exc:
                logger.error(f"Failed to send rejection notification: {notif_exc}", exc_info=True)
            
            return response_data
        except Exception as exc:
            return self.handle_exception(exc)


class EventParticipationListView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/events/<int:event_id>/participations/
    Event admin lists all participation requests for an event
    Query Params: ?status=pending|accepted|rejected
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = get_object_or_404(Event, pk=event_id)
            
            # # Check if user is event admin
            # if event.shop_admin != request.user:
            #     return self.error_response(message="Not authorized")
            
            queryset = EventParticipant.objects.filter(event=event)
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter in ('accepted', 'rejected', 'pending'):
                queryset = queryset.filter(status=status_filter)
            
            queryset = queryset.order_by('-created_at')
            serializer = EventParticipantListSerializer(
                queryset,
                many=True,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Event participations retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== SHOP OWNER: MY EVENTS WITH CHECK-INS ====================

class MyEventsWithCheckInsListView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-events-with-checkins/
    Shop owner sees all events their shops are in + users who checked in their shops
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all events where current shop owner has shops
            queryset = EventShop.objects.filter(
                shop__shop_owner=request.user,
                status='accepted'  # Only accepted shops
            ).order_by('-created_at')
            
            serializer = ShopOwnerEventWithShopsSerializer(
                queryset,
                many=True,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="My events with check-ins retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyEventsWithCheckInsDetailView(BaseResponseMixin, APIView):
    """
    GET /api/shopowner/my-events-with-checkins/{event_id}/
    Shop owner sees detailed view of one event with their shops and all check-ins
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = get_object_or_404(Event, pk=event_id)
            
            # Get all event-shop combinations for this owner in this event
            queryset = EventShop.objects.filter(
                event=event,
                shop__shop_owner=request.user,
                status='accepted'
            )
            
            if not queryset.exists():
                return self.error_response(
                    message="You have no shops in this event"
                )
            
            # Return first one (or could return all if owner has multiple shops in same event)
            event_shop = queryset.first()
            
            serializer = ShopOwnerEventWithShopsSerializer(
                event_shop,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Event details retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)