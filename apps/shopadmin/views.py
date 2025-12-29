"""
Shop Admin Views - Event Management
Clean class-based views without ViewSets
"""

from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status, generics
from rest_framework.response import Response

from apps.core.utils.mixins import BaseResponseMixin
from .models import Event, EventShop, EventShopParticipant, EventPassport
from .serializers import (
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    ParticipantListSerializer, ParticipantUpdateSerializer,
    PassportListSerializer, PassportDetailSerializer, PassportCreateSerializer,
    EventApproveRejectSerializer, EventAdminEventWithCheckInsSerializer
)

from rest_framework.parsers import MultiPartParser, FormParser

# ==================== EVENT VIEWS ====================

class EventListView(BaseResponseMixin, APIView):
    """List all events with filtering"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            queryset = Event.objects.filter(status='approved')
            
            # Filter by shop_admin
            shop_admin = request.query_params.get('shop_admin')
            if shop_admin:
                queryset = queryset.filter(shop_admin_id=shop_admin)
            
            # Filter by date range
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            if from_date:
                queryset = queryset.filter(from_date__gte=from_date)
            if to_date:
                queryset = queryset.filter(to_date__lte=to_date)
            
            # Search by name or location
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(location__icontains=search)
                )
            
            queryset = queryset.order_by('-created_at')
            serializer = EventListSerializer(queryset, many=True, context={'request': request})
            
            return self.success_response(
                data=serializer.data,
                message="Events retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class EventDetailView(BaseResponseMixin, APIView):
    """Get single event details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            event = get_object_or_404(Event, pk=pk)
            serializer = EventDetailSerializer(event)
            
            return self.success_response(
                data=serializer.data,
                message="Event retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class EventCreateView(BaseResponseMixin, APIView):
    """Create new event with multiple images"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            serializer = EventCreateUpdateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            event = serializer.save()

            response_serializer = EventDetailSerializer(
                event,
                context={'request': request}
            )
            return self.created_response(
                data=response_serializer.data,
                message="Event created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
        

class EventUpdateView(BaseResponseMixin, APIView):
    """Update existing event"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        try:
            event = get_object_or_404(Event, pk=pk)
            serializer = EventCreateUpdateSerializer(event, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            event = serializer.save()
            
            response_serializer = EventDetailSerializer(event)
            return self.updated_response(
                data=response_serializer.data,
                message="Event updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def patch(self, request, pk):
        return self.put(request, pk)


class EventDeleteView(BaseResponseMixin, APIView):
    """Delete event"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            event = get_object_or_404(Event, pk=pk)
            event.delete()
            
            return self.deleted_response(message="Event deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)

# ==================== PARTICIPANT MANAGEMENT ====================

class ParticipantListView(BaseResponseMixin, APIView):
    """List all participants with filtering"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            queryset = EventShopParticipant.objects.all()
            
            # Filter by event_shop
            event_shop = request.query_params.get('event_shop')
            if event_shop:
                queryset = queryset.filter(event_shop_id=event_shop)
            
            # Filter by event
            event = request.query_params.get('event')
            if event:
                queryset = queryset.filter(event_shop__event_id=event)
            

            rejected = request.query_params.get('rejected')
            if rejected is not None:
                queryset = queryset.filter(rejected=rejected.lower() == 'true')
        
            
            queryset = queryset.order_by('-created_at')
            serializer = ParticipantListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Participants retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ParticipantDetailView(BaseResponseMixin, APIView):
    """Get participant details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            participant = get_object_or_404(EventShopParticipant, pk=pk)
            serializer = ParticipantListSerializer(participant)
            
            return self.success_response(
                data=serializer.data,
                message="Participant retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ParticipantDeleteView(BaseResponseMixin, APIView):
    """Delete participant"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            participant = get_object_or_404(EventShopParticipant, pk=pk)
            participant.delete()
            
            return self.deleted_response(message="Participant deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class ParticipantRequestsListView(BaseResponseMixin, APIView):
    """List pending participant requests for an event (admin only)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, event_pk):
        try:
            event = get_object_or_404(Event, pk=event_pk)
            # Only event admin can view requests
            if event.shop_admin != request.user:
                return self.error_response(message="Not authorized", status=status.HTTP_403_FORBIDDEN)

            queryset = EventShopParticipant.objects.filter(
                event_shop__event=event,
                status='pending'
            ).order_by('-created_at')

            serializer = ParticipantListSerializer(queryset, many=True, context={'request': request})
            return self.success_response(
                data=serializer.data,
                message="Pending participant requests retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ParticipantApproveView(BaseResponseMixin, APIView):
    """Approve a participant request (admin only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            participant = get_object_or_404(EventShopParticipant, pk=pk)

            # Only event admin can approve
            if participant.event_shop.event.shop_admin != request.user:
                return self.error_response(message="Not authorized", status=status.HTTP_403_FORBIDDEN)

            participant.status = 'accepted'
            participant.save()

            serializer = ParticipantListSerializer(participant)
            return self.success_response(
                data=serializer.data,
                message="Participant request approved"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ParticipantRejectView(BaseResponseMixin, APIView):
    """Reject a participant request (admin only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            participant = get_object_or_404(EventShopParticipant, pk=pk)

            # Only event admin can reject
            if participant.event_shop.event.shop_admin != request.user:
                return self.error_response(message="Not authorized", status=status.HTTP_403_FORBIDDEN)

            participant.status = 'rejected'
            participant.save()

            return self.success_response(
                message="Participant request rejected"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== PASSPORT MANAGEMENT ====================

class PassportListView(BaseResponseMixin, APIView):
    """List all passports with filtering"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            queryset = EventPassport.objects.all()
            
            # Filter by event
            event = request.query_params.get('event')
            if event:
                queryset = queryset.filter(event_id=event)
            
            # Filter by shop
            shop = request.query_params.get('shop')
            if shop:
                queryset = queryset.filter(shop_id=shop)
            
            # Filter by passport_id
            passport_id = request.query_params.get('passport_id')
            if passport_id:
                queryset = queryset.filter(passport_id__icontains=passport_id)
            
            queryset = queryset.order_by('-created_at')
            serializer = PassportListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Passports retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class PassportDetailView(BaseResponseMixin, APIView):
    """Get passport details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            passport = get_object_or_404(EventPassport, pk=pk)
            serializer = PassportDetailSerializer(passport)
            
            return self.success_response(
                data=serializer.data,
                message="Passport retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class PassportCreateView(BaseResponseMixin, APIView):
    """Create new passport"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = PassportCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            passport = serializer.save()
            
            response_serializer = PassportDetailSerializer(passport)
            return self.created_response(
                data=response_serializer.data,
                message="Passport created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class PassportUpdateView(BaseResponseMixin, APIView):
    """Update passport"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        try:
            passport = get_object_or_404(EventPassport, pk=pk)
            serializer = PassportCreateSerializer(passport, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            passport = serializer.save()
            
            response_serializer = PassportDetailSerializer(passport)
            return self.updated_response(
                data=response_serializer.data,
                message="Passport updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
    
    def patch(self, request, pk):
        return self.put(request, pk)


class PassportDeleteView(BaseResponseMixin, APIView):
    """Delete passport"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            passport = get_object_or_404(EventPassport, pk=pk)
            passport.delete()
            
            return self.deleted_response(message="Passport deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)
        

class MyEventsListAPIView(generics.ListAPIView):

    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Event.objects.filter(
            shop_admin=self.request.user
        ).prefetch_related('images').order_by('-created_at')
    


# ===== SUPERADMIN APIS =====

class SuperAdminEventListAPIView(generics.ListAPIView):

    serializer_class = EventListSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Event.objects.all().select_related('shop_admin').prefetch_related('images')
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(location__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class SuperAdminEventDetailAPIView(generics.RetrieveAPIView):

    queryset = Event.objects.all()
    serializer_class = EventDetailSerializer
    permission_classes = [IsAdminUser]


class SuperAdminEventApproveRejectAPIView(APIView):

    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {'error': 'Event not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EventApproveRejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        
        # Update status based on action
        if action == 'approve':
            event.status = 'approved'
            message = f'Event "{event.name}" has been APPROVED!'
        else:  # reject
            event.status = 'rejected'
            message = f'Event "{event.name}" has been REJECTED!'
        
        event.save()
        
        return Response({
            'message': message,
            'event': EventDetailSerializer(event).data
        }, status=status.HTTP_200_OK)


# ==================== EVENT ADMIN: MY EVENTS WITH ALL CHECK-INS ====================

class MyEventsWithAllCheckInsListView(BaseResponseMixin, APIView):
    """
    GET /api/shopadmin/my-events-with-checkins/
    Event admin sees all their events + all shops in each + all check-ins per shop
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all events created by current admin
            queryset = Event.objects.filter(
                shop_admin=request.user
            ).order_by('-created_at')
            
            serializer = EventAdminEventWithCheckInsSerializer(
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


class MyEventsWithAllCheckInsDetailView(BaseResponseMixin, APIView):
    """
    GET /api/shopadmin/my-events-with-checkins/{event_id}/
    Event admin sees detailed view of one event with all shops and their check-ins
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = get_object_or_404(Event, pk=event_id, shop_admin=request.user)
            
            serializer = EventAdminEventWithCheckInsSerializer(
                event,
                context={'request': request}
            )
            
            return self.success_response(
                data=serializer.data,
                message="Event details with check-ins retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)