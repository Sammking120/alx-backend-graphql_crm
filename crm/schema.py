# File: crm/schema.py
# This file defines the GraphQL schema for the CRM application, including types, inputs, and
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction, IntegrityError
from .models import Customer, Product, Order
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime


class CustomerType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    email = graphene.String()
    phone = graphene.String()

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'order_date', 'total_amount')

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
    index = graphene.Int()
    message = graphene.String()

    def __init__(self, index=None, message=None, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.message = message

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
                errors.append(ErrorType(index=index, message=str(e)))
        
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
                order.save()  # Triggers total_amount calculation
                return CreateOrder(order=order) # type: ignore
        except Exception as e:
            raise Exception(f"Error creating order: {str(e)}")

class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(self, info):
        return "Hello, GraphQL!"

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(mutation=Mutation)

