from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime, timedelta
import logging

# Set up logging to /tmp/order_reminders_log.txt
logging.basicConfig(
    filename='/tmp/order_reminders_log.txt',
    level=logging.INFO,
    format='%(asctime)s - Order ID: %(message)s'
)

# Set up GraphQL client
transport = AIOHTTPTransport(url="http://localhost:8000/graphql")
client = Client(transport=transport, fetch_schema_from_transport=True)

# Define GraphQL query for orders within the last 7 days
query = gql("""
    query {
        orders(orderDate_Gte: "%s") {
            id
            customer {
                email
            }
        }
    }
""" % (datetime.now() - timedelta(days=7)).isoformat())

# Execute query and log results
async def main():
    async with client as session:
        result = await session.execute(query)
        for order in result['orders']:
            logging.info(f"{order['id']} - Customer Email: {order['customer']['email']}")
    print("Order reminders processed!")

# Run the async function
import asyncio
asyncio.run(main())