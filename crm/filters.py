# crm/filters.py
import django_filters
from django_filters import CharFilter, NumberFilter, DateTimeFilter, IsoDateTimeFilter
from .models import Customer, Product, Order
from django.db.models import Q

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    created_at__gte = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern')
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at__gte', 'created_at__lte', 'phone_pattern']
    
    def filter_phone_pattern(self, queryset, name, value):
        if value.startswith('+1'):
            return queryset.filter(phone__startswith='+1')
        return queryset

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    price__gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price__lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    stock__gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock__lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    
    class Meta:
        model = Product
        fields = ['name', 'price__gte', 'price__lte', 'stock__gte', 'stock__lte', 'low_stock']
    
    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

class OrderFilter(django_filters.FilterSet):
    total_amount__gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount__lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date__gte = django_filters.IsoDateTimeFilter(field_name='order_date', lookup_expr='gte')
    order_date__lte = django_filters.IsoDateTimeFilter(field_name='order_date', lookup_expr='lte')
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains')
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains')
    product_id = django_filters.NumberFilter(field_name='products__id', lookup_expr='exact')
    
    class Meta:
        model = Order
        fields = ['total_amount__gte', 'total_amount__lte', 'order_date__gte', 'order_date__lte', 
                 'customer_name', 'product_name', 'product_id']


