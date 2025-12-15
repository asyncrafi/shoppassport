"""
Shopper Views - Passport and Check-in Management
Clean class-based views without ViewSets
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.core.utils.mixins import BaseResponseMixin
from apps.shopadmin.models import EventPassport, ShopperCheckIn
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
    """Shopper checks in by scanning QR code"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Add current user as shopper
            data = request.data.copy()
            data['shopper'] = request.user.id
            
            serializer = CheckInCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            check_in = serializer.save()
            
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