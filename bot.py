import requests
import pymongo
import random
import time

# MongoDB Connection
client = pymongo.MongoClient("mongodb+srv://VladislavKon:<PassWord>@cluster0.trc6kgd.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database("Cluster0")
users_collection = db.get_collection("users")

# Anilist API Endpoint
ANILIST_API_URL = "https://api.anilist.co/graphql"

# Function to check new comments for a specific post
def check_new_comments(post_id):
    query = """
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
    """
    variables = {
        "id": post_id
    }
    response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
    data = response.json()
    comments = data["data"]["Media"]["comments"]
    return comments

# Function to send a message to a user
def send_message(user_id, message):
    # Implement your message sending logic here
    print(f"Sent message to user {user_id}: {message}")

# Main function
def main():
    post_id = 626828396  # Replace this with the specific post ID you want to monitor

    while True:
        # Check for new comments
        comments = check_new_comments(post_id)

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
                # Send message to the user
                send_message(user_id, message)

        # Wait for an hour before checking for new comments again
        time.sleep(3600)

if __name__ == "__main__":
    main()
