#!/usr/bin/python3
"""
Telegram → PostgreSQL Data Collection Script
--------------------------------------------

Required Libraries:
    pip install telethon psycopg2-binary
"""

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, PeerUser
import psycopg2
import asyncio

# -----------------------------------------------------------------------------
# Database Configuration (placeholder)
# -----------------------------------------------------------------------------
# For replication purposes, database connection details are intentionally omitted.
# Example structure only — replace with your secure local configuration.
db_config = {
    'dbname': 'your_database_name',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost'
}

# -----------------------------------------------------------------------------
# Telegram API Credentials (placeholder)
# -----------------------------------------------------------------------------
# Replace with your credentials obtained from https://my.telegram.org

api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone = '+00000000000'  # optional; used for login on first run


# -----------------------------------------------------------------------------
# Core Database Functions
# -----------------------------------------------------------------------------
def get_all_telegram_channels(connection):
    """
    Returns a list of Telegram channel usernames from a local table.
    Example structure (not published):
        telegram_channels(channel_username TEXT PRIMARY KEY)
    """
    cursor = connection.cursor()
    query = "SELECT channel_username FROM telegram_channels;"
    cursor.execute(query)
    rows = cursor.fetchall()
    channels_list = [{"channel_username": row[0]} for row in rows]
    return channels_list


def create_db_connection(db_config):
    """Establishes a connection to PostgreSQL (local or containerized instance)."""
    connection = psycopg2.connect(
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host']
    )
    return connection


def insert_messages_to_db(messages, connection):
    """
    Inserts message metadata into a local table.
    Example structure (not published):
        telegram_data(channel_id BIGINT, message_id BIGINT, message TEXT, ...)
    """
    try:
        with connection.cursor() as cursor:
            insert_query = """
            INSERT INTO telegram_data (
                channel_id, message_id, channel_name, time, message,
                views, reposts, forward_from_id, forward_channel_username, forward_channel_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for message in messages:
                cursor.execute(insert_query, (
                    str(message['channel_id']),
                    message['message_id'],
                    message['channel_name'],
                    message['time'],
                    message['message'],
                    message['views'],
                    message['reposts'],
                    message['forward_from_id'],
                    message['forward_channel_username'],
                    message['forward_channel_name']
                ))
        connection.commit()
    except Exception as e:
        print(f"Error inserting messages: {e}")
        connection.rollback()


def get_max_message_id(connection, channel_id):
    """Returns the maximum stored message_id for a given channel (used for pagination)."""
    cursor = connection.cursor()
    try:
        query = f"""
        SELECT MAX(message_id)
        FROM telegram_data
        WHERE channel_id = '{channel_id}'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else 0
    except Exception as e:
        print(f"Error fetching max message_id: {str(e)}")
        return None
    finally:
        cursor.close()


# -----------------------------------------------------------------------------
# Telegram Data Retrieval Functions
# -----------------------------------------------------------------------------
async def get_channel_info(client, channel_username):
    """Retrieves full metadata for a public Telegram channel."""
    await client.start()
    entry = await client(GetFullChannelRequest(channel_username))
    return entry


def create_chanal_info(connection, channel_info):
    """Updates local table with channel metadata (not published)."""
    cursor = connection.cursor()

    channel_id = channel_info.chats[0].id
    channel_name = channel_info.chats[0].title
    channel_username = channel_info.chats[0].username
    participants_count = channel_info.full_chat.participants_count
    channel_created = str(channel_info.chats[0].date)
    channel_description = channel_info.full_chat.about

    query = """
        UPDATE telegram_channels
        SET channel_id = %s,
            channel_name = %s,
            participants_count = %s,
            channel_created = %s,
            channel_description = %s
        WHERE channel_username = %s
    """
    cursor.execute(query, (
        channel_id,
        channel_name,
        participants_count,
        channel_created,
        channel_description,
        channel_username
    ))
    connection.commit()
    cursor.close()


async def fetch_and_save_messages(client, channel_id, offset_db, channel_username, channel_name, progress):
    """
    Fetches message history for a Telegram channel and prepares it for storage.
    Only public messages are collected; private or deleted content is excluded.
    """
    all_messages = []
    offset_id = offset_db + 500

    # Retrieve last message ID for progress output
    history = await client(GetHistoryRequest(
        peer=PeerChannel(channel_id),
        limit=1,
        offset_id=0,
        offset_date=None,
        add_offset=0,
        max_id=0,
        min_id=0,
        hash=0
    ))
    msg_in_channel = history.messages[0].id if history.messages else "unknown"

    print(progress, "| Channel ID:", channel_id,
          "| Username:", channel_username,
          "| Name:", channel_name,
          "| Saved:", offset_db, "/", msg_in_channel)

    limit = 100

    while True:
        history = await client(GetHistoryRequest(
            peer=PeerChannel(channel_id),
            offset_id=0,
            add_offset=5600,
            max_id=0,
            min_id=0,
            limit=limit,
            offset_date=None,
            hash=0
        ))

        if not history.messages:
            break

        messages = history.messages
        for message in messages:
            if not message.message:
                continue

            forward_from_id = None
            forward_channel_name = None
            forward_channel_username = None

            if message.fwd_from:
                if isinstance(message.fwd_from.from_id, PeerChannel):
                    forward_from_id = message.fwd_from.from_id.channel_id
                    try:
                        channel = await client.get_entity(message.fwd_from.from_id.channel_id)
                        forward_channel_name = channel.title
                        forward_channel_username = channel.username
                    except Exception:
                        forward_channel_name = "unknown"
                        forward_channel_username = "unknown"
                elif isinstance(message.fwd_from.from_id, PeerUser):
                    forward_channel_name = "unknown"
                    forward_channel_username = "unknown"

            views = message.views or 0
            reposts = message.forwards or 0

            all_messages.append({
                'message_id': message.id,
                'channel_id': channel_id,
                'channel_name': channel_name,
                'time': message.date,
                'message': message.message,
                'forward_from_id': forward_from_id,
                'forward_channel_name': forward_channel_name,
                'forward_channel_username': forward_channel_username,
                'views': views,
                'reposts': reposts
            })

        max_id = messages[-1].id

    print("Fetched messages:", len(all_messages))
    return all_messages


# -----------------------------------------------------------------------------
# Main Async Workflow
# -----------------------------------------------------------------------------
async def main():
    """
    Main entry point:
    - Connects to database
    - Iterates over known public Telegram channels
    - Downloads and stores their messages and metadata
    """
    conn = create_db_connection(db_config)
    channels = get_all_telegram_channels(conn)
    client = TelegramClient('session_name', api_id, api_hash)

    for index, item in enumerate(channels, start=1):
        progress = f"Processing {index}/{len(channels)}: {item['channel_username']}"
        exit_loop = False
        channel_username = "example_channel"  # placeholder for demonstration

        try:
            channel_info = await get_channel_info(client, channel_username)
            create_chanal_info(conn, channel_info)
            channel_id = channel_info.chats[0].id
            channel_name = channel_info.chats[0].title
        except Exception as e:
            print(f"Error processing {channel_username}: {e}")
            continue

        async with client:
            while not exit_loop:
                offset_id = get_max_message_id(conn, channel_id)
                all_messages = await fetch_and_save_messages(
                    client, channel_id, offset_id, channel_username, channel_name, progress
                )
                insert_messages_to_db(all_messages, conn)
                if not all_messages:
                    print("#" * 100)
                    exit_loop = True

    conn.close()


# -----------------------------------------------------------------------------
# Script Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
