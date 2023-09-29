import os
import time
import random
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from pymongo import MongoClient
from redis import Redis
from rq import Queue

# Load configuration from environment variables or .env file
POST_ID = int(os.getenv("POST_ID", "626828396"))
ANILIST_API_URL = os.getenv("ANILIST_API_URL", "https://api.anilist.co/graphql")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# MongoDB Connection
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client.get_database("Cluster0")
users_collection = mongo_db.get_collection("users")

# Redis Connection
redis_conn = Redis.from_url(REDIS_URL)
message_queue = Queue("messages", connection=redis_conn)

# Anilist API Client
transport = RequestsHTTPTransport(url=ANILIST_API_URL)
anilist_client = Client(transport=transport, fetch_schema_from_transport=True)

# GraphQL Queries
QUERY_MEDIA_COMMENTS = gql("""
    query ($id: Int) {
        Media(id: $id) {
            id
            title {
                romaji
            }
            siteUrl
            comments {
                id
                userId
                text
            }
        }
    }
""")
MUTATION_CREATE_MESSAGE_THREAD = gql("""
    mutation ($userId: Int!) {
        createMessageThread(input: {userId: $userId}) {
            messageThread {
                id
            }
        }
    }
""")
MUTATION_CREATE_MESSAGE = gql("""
    mutation ($messageThreadId: Int!, $message: String!) {
        createMessage(input: {messageThreadId: $messageThreadId, message: $message}) {
            message {
                id
            }
        }
    }
""")

# Function to check new comments for a specific post
def check_new_comments(post_id):
    result = anilist_client.execute(QUERY_MEDIA_COMMENTS, variable_values={"id": post_id})
    comments = result["Media"]["comments"]
    return comments

# Function to send a message to a user
def send_message(user_id, message):
    result = anilist_client.execute(MUTATION_CREATE_MESSAGE_THREAD, variable_values={"userId": user_id})
    message_thread_id = result["createMessageThread"]["messageThread"]["id"]
    result = anilist_client.execute(MUTATION_CREATE_MESSAGE, variable_values={"messageThreadId": message_thread_id, "message": message})
    message_id = result["createMessage"]["message"]["id"]
    print(f"Sent message to user {user_id}: {message}")

# Main function
def main():
    while True:
        # Check for new comments
        comments = check_new_comments(POST_ID)

        # Process new comments
        for comment in comments:
            user_id = comment["userId"]
            comment_id = comment["id"]

            # Check if user ID is in the database
            if users_collection.find_one({"user_id": user_id, "comment_id": comment_id}) is None:
                # User ID not found, send a message based on a random number (1-10)
                random_number = random.randint(1, 10)
                message = ""
                if random_number == 4:
                    message = "Hello dude"
                elif random_number == 3:
                    message = "hi baby"
                # Add user ID and comment ID to the database to avoid duplicate messages
                users_collection.insert_one({"user_id": user_id, "comment_id": comment_id})
                # Send message to the user asynchronously
                message_queue.enqueue(send_message, user_id, message)

        # Wait for an hour before checking for new comments again
        time.sleep(3600)

if __name__ == "__main__":
    main()