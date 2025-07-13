from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime
import logging

# Configure logging to append to /tmp/crm_heartbeat_log.txt
logging.basicConfig(
    filename='/tmp/crm_heartbeat_log.txt',
    level=logging.INFO,
    format='%(message)s',
    filemode='a'
)

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
    # Format timestamp as DD/MM/YYYY-HH:MM:SS
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    # Query GraphQL endpoint
    try:
        hello_response = asyncio.run(query_graphql_hello())
        message = f"{timestamp} CRM is alive - GraphQL hello: {hello_response}"
    except Exception as e:
        message = f"{timestamp} CRM is alive - GraphQL error: {str(e)}"
    # Log the message
    logging.info(message)