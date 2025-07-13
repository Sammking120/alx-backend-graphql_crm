from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime
import logging

# Configure logging for heartbeat
logging.basicConfig(
    filename='/tmp/crm_heartbeat_log.txt',
    level=logging.INFO,
    format='%(message)s',
    filemode='a'
)

# Configure logging for low stock updates
low_stock_logger = logging.getLogger('low_stock')
low_stock_handler = logging.FileHandler('/tmp/low_stock_updates_log.txt')
low_stock_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%d/%m/%Y-%H:%M:%S'))
low_stock_logger.addHandler(low_stock_handler)
low_stock_logger.setLevel(logging.INFO)

async def query_graphql_hello():
    """Query the GraphQL hello field to verify endpoint responsiveness."""
    transport = AIOHTTPTransport(url="http://localhost:8000/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql("""
        query {
            hello
        }
    """)
    async with client as session:
        result = await session.execute(query)
        return result.get('hello', 'No response')

def log_crm_heartbeat():
    """Log a heartbeat message and verify GraphQL endpoint."""
    import asyncio
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    try:
        hello_response = asyncio.run(query_graphql_hello())
        message = f"{timestamp} CRM is alive - GraphQL hello: {hello_response}"
    except Exception as e:
        message = f"{timestamp} CRM is alive - GraphQL error: {str(e)}"
    logging.info(message)

async def update_low_stock_products():
    """Execute GraphQL mutation to update low-stock products."""
    transport = AIOHTTPTransport(url="http://localhost:8000/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    mutation = gql("""
        mutation {
            updateLowStockProducts {
                successMessage
                updatedProducts {
                    name
                    stock
                }
            }
        }
    """)
    async with client as session:
        result = await session.execute(mutation)
        return result['updateLowStockProducts']

def update_low_stock():
    """Run the low-stock update mutation and log results."""
    import asyncio
    try:
        result = asyncio.run(update_low_stock_products())
        for product in result['updatedProducts']:
            low_stock_logger.info(f"Updated {product['name']} to stock: {product['stock']}")
        low_stock_logger.info(result['successMessage'])
    except Exception as e:
        low_stock_logger.error(f"Error updating low-stock products: {str(e)}")