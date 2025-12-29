"""
Shopper Views - Passport and Check-in Management
Clean class-based views without ViewSets
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as rest_status
from rest_framework.response import Response

from apps.core.utils.mixins import BaseResponseMixin
from apps.shopadmin.models import EventPassport, ShopperCheckIn, Event
from apps.shopadmin.serializers import (
    PassportListSerializer, PassportDetailSerializer,
    CheckInListSerializer, CheckInDetailSerializer, CheckInCreateSerializer
)


# ==================== SHOPPER PASSPORTS ====================

class MyPassportListView(BaseResponseMixin, APIView):
    """List all passports for current shopper"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all passports (in real scenario, filter by shopper)
            # For now showing all, you may want to add shopper FK to EventPassport
            queryset = EventPassport.objects.all()
            
            # Filter by event
            event = request.query_params.get('event')
            if event:
                queryset = queryset.filter(event_id=event)
            
            # Filter by validity
            valid_only = request.query_params.get('valid_only')
            if valid_only and valid_only.lower() == 'true':
                from datetime import date
                today = date.today()
                queryset = queryset.filter(
                    valid_from__lte=today,
                    valid_to__gte=today
                )
            
            queryset = queryset.order_by('-created_at')
            serializer = PassportListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Passports retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyPassportDetailView(BaseResponseMixin, APIView):
    """Get passport details with QR code"""
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


class PassportByIdView(BaseResponseMixin, APIView):
    """Get passport by passport_id (for QR scan)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, passport_id):
        try:
            passport = get_object_or_404(EventPassport, passport_id=passport_id)
            serializer = PassportDetailSerializer(passport)
            
            return self.success_response(
                data=serializer.data,
                message="Passport retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== SHOPPER CHECK-INS ====================

class CheckInCreateView(BaseResponseMixin, APIView):
    """
    Shopper checks in by scanning QR code
    Can accept either:
    - event_passport: <passport_pk> (integer)
    - passport_id: <passport_string_id> (e.g., "1-49-abc123")
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Add current user as shopper
            data = request.data.copy()
            data['shopper'] = request.user.id
            
            # If passport_id (string) is provided, resolve to event_passport (PK)
            if 'passport_id' in data and 'event_passport' not in data:
                passport = get_object_or_404(
                    EventPassport,
                    passport_id=data['passport_id']
                )
                data['event_passport'] = passport.id
                # Remove passport_id from data since serializer expects event_passport
                data.pop('passport_id')
            
            serializer = CheckInCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            check_in = serializer.save()
            
            # Mark passport as visited
            passport = check_in.event_passport
            passport.is_visited = True
            passport.total_visits = passport.check_ins.count()
            passport.save()
            
            response_serializer = CheckInDetailSerializer(check_in)
            return self.created_response(
                data=response_serializer.data,
                message="Check-in successful"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyCheckInListView(BaseResponseMixin, APIView):
    """List all check-ins for current shopper"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            queryset = ShopperCheckIn.objects.filter(shopper=request.user)
            
            # Filter by event
            event = request.query_params.get('event')
            if event:
                queryset = queryset.filter(event_passport__event_id=event)
            
            # Filter by shop
            shop = request.query_params.get('shop')
            if shop:
                queryset = queryset.filter(event_passport__shop_id=shop)
            
            # Filter by date range
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            if from_date:
                queryset = queryset.filter(check_in_time__date__gte=from_date)
            if to_date:
                queryset = queryset.filter(check_in_time__date__lte=to_date)
            
            queryset = queryset.order_by('-check_in_time')
            serializer = CheckInListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Check-ins retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyCheckInDetailView(BaseResponseMixin, APIView):
    """Get check-in details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            check_in = get_object_or_404(
                ShopperCheckIn,
                pk=pk,
                shopper=request.user
            )
            serializer = CheckInDetailSerializer(check_in)
            
            return self.success_response(
                data=serializer.data,
                message="Check-in retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class MyCheckInStatsView(BaseResponseMixin, APIView):
    """Get check-in statistics for current shopper"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            from django.db.models import Count
            from datetime import date, timedelta
            
            # Total check-ins
            total_check_ins = ShopperCheckIn.objects.filter(
                shopper=request.user
            ).count()
            
            # Check-ins today
            today = date.today()
            check_ins_today = ShopperCheckIn.objects.filter(
                shopper=request.user,
                check_in_time__date=today
            ).count()
            
            # Check-ins this week
            week_ago = today - timedelta(days=7)
            check_ins_this_week = ShopperCheckIn.objects.filter(
                shopper=request.user,
                check_in_time__date__gte=week_ago
            ).count()
            
            # Unique events visited
            unique_events = ShopperCheckIn.objects.filter(
                shopper=request.user
            ).values('event_passport__event').distinct().count()
            
            # Unique shops visited
            unique_shops = ShopperCheckIn.objects.filter(
                shopper=request.user
            ).values('event_passport__shop').distinct().count()
            
            # Recent check-ins
            recent_check_ins = ShopperCheckIn.objects.filter(
                shopper=request.user
            ).order_by('-check_in_time')[:5]
            
            recent_serializer = CheckInListSerializer(recent_check_ins, many=True)
            
            data = {
                'total_check_ins': total_check_ins,
                'check_ins_today': check_ins_today,
                'check_ins_this_week': check_ins_this_week,
                'unique_events': unique_events,
                'unique_shops': unique_shops,
                'recent_check_ins': recent_serializer.data
            }
            
            return self.success_response(
                data=data,
                message="Statistics retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== PUBLIC PASSPORT & EVENT INFO ====================

class PublicEventPassportsView(BaseResponseMixin, APIView):
    """Get all passports for a specific event (for shoppers to browse)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            queryset = EventPassport.objects.filter(event_id=event_id)
            
            # Only show valid passports
            from datetime import date
            today = date.today()
            queryset = queryset.filter(
                valid_from__lte=today,
                valid_to__gte=today
            )
            
            serializer = PassportListSerializer(queryset, many=True)
            
            return self.success_response(
                data=serializer.data,
                message="Event passports retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== SHOPPER EVENT BROWSING ====================

class EventListView(BaseResponseMixin, APIView):
    """List all upcoming and ongoing events"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            from datetime import date
            today = date.today()
            
            # Get status filter
            event_status = request.query_params.get('status')  # upcoming, ongoing, completed
            
            queryset = Event.objects.all()
            
            if event_status == 'upcoming':
                queryset = queryset.filter(from_date__gt=today)
            elif event_status == 'ongoing':
                queryset = queryset.filter(from_date__lte=today, to_date__gte=today)
            elif event_status == 'completed':
                queryset = queryset.filter(to_date__lt=today)
            
            # Search by name
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(name__icontains=search)
            
            queryset = queryset.order_by('-from_date')
            
            # Return only basic event info with passport count
            data = []
            for event in queryset:
                passport_count = event.passports.count()
                data.append({
                    'id': event.id,
                    'name': event.name,
                    'location': event.location,
                    'from_date': event.from_date,
                    'to_date': event.to_date,
                    'total_shops': passport_count,
                    'status': 'upcoming' if event.from_date > today else ('ongoing' if event.to_date >= today else 'completed')
                })
            
            return self.success_response(
                data=data,
                message="Events retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class EventShopsView(BaseResponseMixin, APIView):
    """List all shops (passports) in an event with visit status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = get_object_or_404(Event, pk=event_id)
            
            # Get all passports for this event
            passports = EventPassport.objects.filter(event=event).order_by('shop__shop_name')
            print(event, "event found 🍒🍒🍒🍒")
            print(passports, "passports found 🍒🍒🍒🍒")
            
            # Check which shops current shopper has visited
            visited_shop_ids = ShopperCheckIn.objects.filter(
                shopper=request.user,
                event_passport__event=event
            ).values_list('event_passport__shop_id', flat=True).distinct()
            
            data = []
            for passport in passports:
                check_in_count = passport.check_ins.count()
                data.append({
                    'passport_id': passport.id,
                    'passport_qr_id': passport.passport_id,
                    'shop_id': passport.shop.id,
                    'shop_name': passport.shop.shop_name,
                    'shop_location': passport.shop.shop_location,
                    'shop_logo': request.build_absolute_uri(passport.shop.shop_logo.url) if passport.shop.shop_logo else None,
                    'qr_code_url': request.build_absolute_uri(passport.shop_qr_code.url) if passport.shop_qr_code else None,
                    'is_visited': passport.shop.id in visited_shop_ids,
                    'total_visits': check_in_count,
                    'valid_from': passport.valid_from,
                    'valid_to': passport.valid_to
                })
            
            return self.success_response(
                data=data,
                message="Event shops retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ShopVisitDetailsView(BaseResponseMixin, APIView):
    """Get detailed visit info for a shop (who visited, when, etc)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id, shop_id):
        try:
            # Get all check-ins for this shop in this event
            check_ins = ShopperCheckIn.objects.filter(
                event_passport__event_id=event_id,
                event_passport__shop_id=shop_id
            ).order_by('-check_in_time')
            
            # Get passport details
            passport = get_object_or_404(
                EventPassport,
                event_id=event_id,
                shop_id=shop_id
            )
            
            # Build visit details
            visits = []
            for check_in in check_ins:
                visits.append({
                    'id': check_in.id,
                    'shopper_name': check_in.shopper.get_full_name(),
                    'shopper_email': check_in.shopper.email,
                    'check_in_time': check_in.check_in_time,
                    'status': 'stamped'  # Assuming all check-ins are stamped
                })
            
            data = {
                'passport_id': passport.passport_id,
                'shop_name': passport.shop.shop_name,
                'shop_location': passport.shop.shop_location,
                'event_name': passport.event.name,
                'total_visits': len(visits),
                'visits': visits
            }
            
            return self.success_response(
                data=data,
                message="Visit details retrieved successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ==================== QR CODE DOWNLOAD ====================

class DownloadQRCodeView(APIView):
    """Download QR code for a passport (for shop owner)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, passport_id):
        try:
            passport = get_object_or_404(EventPassport, pk=passport_id)
            
            # Check if user is shop owner
            if passport.shop.shop_owner != request.user:
                return Response(
                    {"success": False, "message": "Not authorized"},
                    status=rest_status.HTTP_403_FORBIDDEN
                )
            
            if not passport.shop_qr_code:
                return Response(
                    {"success": False, "message": "QR code not available"},
                    status=rest_status.HTTP_404_NOT_FOUND
                )
            
            # Return QR code file
            return Response({
                "success": True,
                "data": {
                    "qr_code_url": request.build_absolute_uri(passport.shop_qr_code.url),
                    "passport_id": passport.passport_id,
                    "shop_name": passport.shop.shop_name,
                    "event_name": passport.event.name
                },
                "message": "QR code retrieved successfully"
            })
            
        except Exception as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR
            )