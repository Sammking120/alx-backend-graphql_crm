#!/bin/bash

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Run Django command to delete inactive customers and capture count
DELETED_COUNT=$(python manage.py shell -c "from django.utils import timezone; from datetime import timedelta; from crm.models import Customer; count = Customer.objects.filter(last_order_date__lt=timezone.now() - timedelta(days=365)).delete()[0]; print(count)")

# Log the result with timestamp
echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers" >> /tmp/customer_cleanup_log.txt
