# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from .models import Event, EventEntryFee, EventAdminPayment, EarningsSummary
from .serializers import (
    EventEntryFeeSerializer, 
    EventAdminPaymentSerializer,
    VerifyAdminPaymentSerializer,
    EarningsSummarySerializer,
    EarningsOverviewSerializer
)


# ============ FOR EVENT ADMINS ============

class EventEntryFeeView(APIView):
    """Get active entry fee"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            fee = EventEntryFee.objects.filter(is_active=True).first()
            if not fee:
                return Response(
                    {'error': 'No active entry fee configured'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = EventEntryFeeSerializer(fee)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyAdminPaymentView(APIView):
    """Verify payment after event admin pays"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = VerifyAdminPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            event = Event.objects.get(id=data['event_id'], shop_admin=request.user)
            entry_fee = EventEntryFee.objects.filter(is_active=True).first()
            
            if not entry_fee:
                return Response({'error': 'No active entry fee'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already paid
            if hasattr(event, 'admin_payment') and event.admin_payment.status == 'completed':
                return Response(
                    {'error': 'This event entry fee is already paid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check duplicate transaction
            if EventAdminPayment.objects.filter(
                revenuecat_transaction_id=data['revenuecat_transaction_id']
            ).exists():
                return Response(
                    {'error': 'Transaction already processed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create payment
            payment = EventAdminPayment.objects.create(
                event=event,
                event_admin=request.user,
                entry_fee=entry_fee,
                revenuecat_transaction_id=data['revenuecat_transaction_id'],
                revenuecat_user_id=data['revenuecat_user_id'],
                revenuecat_product_id=data['revenuecat_product_id'],
                amount_paid=entry_fee.amount,
                currency=entry_fee.currency,
                platform=data['platform'],
                store_transaction_id=data.get('store_transaction_id', ''),
                status='completed',
                verified_at=timezone.now()
            )
            
            # Approve event
            event.status = 'approved'
            event.save()
            
            # Update earnings summary
            EarningsSummary.update_summary(payment.payment_year, payment.payment_month)
            
            return Response(
                {
                    'success': True,
                    'message': 'Payment verified successfully',
                    'payment': EventAdminPaymentSerializer(payment).data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Event.DoesNotExist:
            return Response(
                {'error': 'Event not found or you are not the owner'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MyPaymentsView(APIView):
    """Event admin's payment history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = EventAdminPayment.objects.filter(
            event_admin=request.user
        ).select_related('event', 'entry_fee').order_by('-payment_date')
        
        serializer = EventAdminPaymentSerializer(payments, many=True)
        return Response(serializer.data)


class CheckEventPaymentView(APIView):
    """Check if event is paid"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
            
            payment = None
            is_paid = False
            
            if hasattr(event, 'admin_payment'):
                payment = event.admin_payment
                is_paid = payment.status == 'completed'
            
            return Response({
                'event_id': event.id,
                'event_name': event.name,
                'is_paid': is_paid,
                'event_status': event.status,
                'payment': EventAdminPaymentSerializer(payment).data if payment else None
            })
            
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)


# ============ FOR SUPER ADMIN DASHBOARD ============

class EarningsOverviewView(APIView):
    """Main earnings overview for super admin dashboard"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            now = timezone.now()
            current_year = now.year
            current_month = now.month
            
            # Total revenue (all time)
            total_stats = EventAdminPayment.objects.filter(
                status='completed'
            ).aggregate(
                total_revenue=Sum('amount_paid'),
                total_transactions=Count('id')
            )
            
            # This year revenue
            year_revenue = EventAdminPayment.objects.filter(
                status='completed',
                payment_year=current_year
            ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            
            # This month revenue
            month_revenue = EventAdminPayment.objects.filter(
                status='completed',
                payment_year=current_year,
                payment_month=current_month
            ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            
            # Last month for growth calculation
            last_month = current_month - 1 if current_month > 1 else 12
            last_month_year = current_year if current_month > 1 else current_year - 1
            
            last_month_revenue = EventAdminPayment.objects.filter(
                status='completed',
                payment_year=last_month_year,
                payment_month=last_month
            ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            
            # Growth percentage
            if last_month_revenue > 0:
                growth = ((month_revenue - last_month_revenue) / last_month_revenue) * 100
            else:
                growth = 100.0 if month_revenue > 0 else 0.0
            
            # Platform breakdown
            platform_stats = EventAdminPayment.objects.filter(
                status='completed'
            ).values('platform').annotate(
                revenue=Sum('amount_paid'),
                count=Count('id')
            )
            
            platform_breakdown = {}
            for stat in platform_stats:
                platform_breakdown[stat['platform']] = {
                    'revenue': float(stat['revenue']),
                    'transactions': stat['count']
                }
            
            # Monthly earnings for last 12 months
            monthly_data = []
            for i in range(11, -1, -1):
                date = now - timedelta(days=i*30)
                month = date.month
                year = date.year
                
                month_rev = EventAdminPayment.objects.filter(
                    status='completed',
                    payment_year=year,
                    payment_month=month
                ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
                
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                monthly_data.append({
                    'month': months[month - 1],
                    'year': year,
                    'revenue': float(month_rev)
                })
            
            overview_data = {
                'total_revenue': total_stats['total_revenue'] or 0,
                'total_transactions': total_stats['total_transactions'] or 0,
                'year_revenue': year_revenue,
                'month_revenue': month_revenue,
                'currency': 'USD',
                'revenue_growth_percentage': round(growth, 2),
                'platform_breakdown': platform_breakdown,
                'monthly_earnings': monthly_data
            }
            
            serializer = EarningsOverviewSerializer(overview_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AllPaymentsView(APIView):
    """All payments for super admin"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Filters
        status_filter = request.query_params.get('status', None)
        platform = request.query_params.get('platform', None)
        year = request.query_params.get('year', None)
        month = request.query_params.get('month', None)
        
        payments = EventAdminPayment.objects.all().select_related(
            'event', 'event_admin', 'entry_fee'
        )
        
        if status_filter:
            payments = payments.filter(status=status_filter)
        if platform:
            payments = payments.filter(platform=platform)
        if year:
            payments = payments.filter(payment_year=int(year))
        if month:
            payments = payments.filter(payment_month=int(month))
        
        payments = payments.order_by('-payment_date')
        
        serializer = EventAdminPaymentSerializer(payments, many=True)
        return Response({
            'count': payments.count(),
            'payments': serializer.data
        })


class MonthlySummaryView(APIView):
    """Monthly summaries for super admin"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        year = request.query_params.get('year', timezone.now().year)
        
        summaries = EarningsSummary.objects.filter(year=year).order_by('-month')
        
        serializer = EarningsSummarySerializer(summaries, many=True)
        return Response(serializer.data)


class RevenueStatsView(APIView):
    """Quick revenue stats"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        now = timezone.now()
        
        # Today
        today_revenue = EventAdminPayment.objects.filter(
            status='completed',
            payment_date__date=now.date()
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # This week
        week_start = now - timedelta(days=now.weekday())
        week_revenue = EventAdminPayment.objects.filter(
            status='completed',
            payment_date__gte=week_start
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # Pending payments
        pending_count = EventAdminPayment.objects.filter(status='pending').count()
        
        return Response({
            'today_revenue': float(today_revenue),
            'week_revenue': float(week_revenue),
            'pending_payments': pending_count,
            'currency': 'USD'
        })


class TopEventAdminsView(APIView):
    """Top paying event admins"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        top_admins = EventAdminPayment.objects.filter(
            status='completed'
        ).values(
            'event_admin__id',
            'event_admin__username',
            'event_admin__email'
        ).annotate(
            total_spent=Sum('amount_paid'),
            event_count=Count('id')
        ).order_by('-total_spent')[:limit]
        
        return Response(list(top_admins))