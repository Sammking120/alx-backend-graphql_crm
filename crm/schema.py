import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction, IntegrityError
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
import graphene
from graphene_django.types import DjangoObjectType
from crm.models import Product

class LowStockProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'stock')

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass

    success_message = graphene.String()
    updated_products = graphene.List(LowStockProductType)

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated_products = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated_products.append(product)
        
        return UpdateLowStockProducts(
            success_message=f"Updated {len(updated_products)} low-stock products",
            updated_products=updated_products
        )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(mutation=Mutation)

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at')
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'order_date', 'total_amount')
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class BulkCustomerInput(graphene.InputObjectType):
    customers = graphene.List(CustomerInput, required=True)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

class ErrorType(graphene.ObjectType):
    index = graphene.Int(required=False)
    message = graphene.String(required=False)

class CustomerFilterInput(graphene.InputObjectType):
    name = graphene.String()
    email = graphene.String()
    created_at__gte = graphene.DateTime()
    created_at__lte = graphene.DateTime()
    phone_pattern = graphene.String()

class ProductFilterInput(graphene.InputObjectType):
    name = graphene.String()
    price__gte = graphene.Decimal()
    price__lte = graphene.Decimal()
    stock__gte = graphene.Int()
    stock__lte = graphene.Int()
    low_stock = graphene.Boolean()

class OrderFilterInput(graphene.InputObjectType):
    total_amount__gte = graphene.Decimal()
    total_amount__lte = graphene.Decimal()
    order_date__gte = graphene.DateTime()
    order_date__lte = graphene.DateTime()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    
    def mutate(self, info, input):
        try:
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone or ''
            )
            customer.full_clean()
            customer.save()
            return CreateCustomer(customer=customer, message="Customer created successfully") # type: ignore
        except ValidationError as e:
            raise Exception(f"Validation error: {str(e)}")
        except IntegrityError:
            raise Exception("Email already exists")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = BulkCustomerInput(required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(ErrorType)
    
    @transaction.atomic
    def mutate(self, info, input):
        customers = []
        errors = []
        
        for index, customer_data in enumerate(input.customers):
            try:
                customer = Customer(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone or ''
                )
                customer.full_clean()
                customer.save()
                customers.append(customer)
            except (ValidationError, IntegrityError) as e:
                errors.append(ErrorType(index=index, message=str(e))) # type: ignore
        
        return BulkCreateCustomers(customers=customers, errors=errors) # type: ignore

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    
    def mutate(self, info, input):
        try:
            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock
            )
            product.full_clean()
            product.save()
            return CreateProduct(product=product) # type: ignore
        except ValidationError as e:
            raise Exception(f"Validation error: {str(e)}")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    
    def mutate(self, info, input):
        try:
            if not input.product_ids:
                raise Exception("At least one product is required")
            
            customer = Customer.objects.filter(id=input.customer_id).first()
            if not customer:
                raise Exception("Invalid customer ID")
            
            products = Product.objects.filter(id__in=input.product_ids)
            if not products or len(products) != len(input.product_ids):
                raise Exception("One or more invalid product IDs")
            
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date or datetime.now()
                )
                order.products.set(products)
                order.save()
                return CreateOrder(order=order) # type: ignore
        except Exception as e:
            raise Exception(f"Error creating order: {str(e)}")

class Query(graphene.ObjectType):
    hello = graphene.String()
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)
    
    def resolve_hello(self, info):
        return "Hello, GraphQL!"
    
    def resolve_all_customers(self, info, **kwargs):
        return CustomerFilter(kwargs).qs
    
    def resolve_all_products(self, info, **kwargs):
        return ProductFilter(kwargs).qs
    
    def resolve_all_orders(self, info, **kwargs):
        return OrderFilter(kwargs).qs

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(mutation=Mutation)


