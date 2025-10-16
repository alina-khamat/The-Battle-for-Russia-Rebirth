# Terms of Service (ToS) Compliance

**Project:** *The Battle for Russia’s Rebirth: Interpreting Pro-War Critical Patriotism and Imperial-Nationalism on Telegram*  
**Authors:** Matthew Blackburn & Alina Khamatdinova  
**Data collection period:** February 2022 – September 2025  
**Interface:** Official **Telegram API** via **Telethon (Python)**.  
No web scraping, browser automation, or reverse engineering was used.

---

## 1. Data Source and Access
All data were obtained **exclusively from publicly accessible Telegram channels** via Telegram’s **official API** using the [Telethon](https://docs.telethon.dev) library.

The collection script relies on the following official API methods:

- `GetFullChannelRequest(channel_username)` — retrieves public metadata of a channel (title, description, participant count).  
- `GetHistoryRequest(PeerChannel(channel_id), …)` — retrieves public message history.  
- `PeerChannel` and `PeerUser` — used only to distinguish forwards originating from channels vs. private user accounts.

The authenticated client was created via `TelegramClient('session_name', api_id, api_hash)` and operated within Telegram’s API usage limits.  
No private chats, private groups, direct messages, invite-only channels, or otherwise restricted content are accessed.

---

## 2. Data Fields Collected and Stored
The database (`telegram_data` in PostgreSQL) stores only information available through the public API.  
Each record contains:

| Field | Description |
|-------|--------------|
| `channel_id` | Numeric channel identifier (from API) |
| `channel_name` | Public title of the channel (string) |
| `message_id` | Message identifier within the channel |
| `time` | Timestamp of the message (UTC) |
| `message` | Text content of the post (UTF-8 encoded) |
| `views` | View count (if available) |
| `reposts` | Number of forwards (if available) |
| `forward_from_id` | Source channel ID if the post is forwarded |
| `forward_channel_name` | Source channel title (if available) |
| `forward_channel_username` | Source channel @username (if available) |

No user-level data, contact information, media attachments, comments, or device/network metadata are collected or stored.  
Only textual message content and basic counters are processed.

---

## 3. Channel Coverage
The dataset includes **public Telegram channels** operated by:
- Media outlets, editorial projects, and political organizations;
- Public figures, commentators, and bloggers **with open, public channels**.

No private user accounts, invite-only groups, or restricted channels are included. If a message is forwarded from a **user account** (`PeerUser`),  the script records `"unknown"` for both `forward_channel_name` and `forward_channel_username`.  
Individual users are not identified.

---

## 4. Handling of Deleted or Unavailable Content
`GetHistoryRequest` returns only currently available messages. Therefore, the collection process retrieves only messages that remain publicly accessible at the time of the API request.  
If a message has been deleted by a channel administrator or has become otherwise unavailable, it is automatically skipped by the script and not included in the database.  
No recovery, archiving, or redistribution of removed or hidden content is attempted, ensuring full compliance with Telegram’s Terms of Service and data-minimization principles.

---

## 5. Platform Compliance and Technical Integrity
- Data collection is **automated through authorized Telegram API calls** using the Telethon library.  
- The script does **not** perform scraping of Telegram web pages, reverse-engineering, or browser automation.  
- Only documented API methods (`GetFullChannelRequest`, `GetHistoryRequest`) are used, with batching (`limit=100`) and pagination.  
- The code respects Telegram’s API rate limits and access controls.  
- API credentials (`api_id`, `api_hash`, phone number, session file) are used solely for authentication and are not included in replication materials.

---


## 6. Data Storage and Access Control
All collected data are stored in a PostgreSQL database hosted on a secure **AWS cloud instance** managed by the research team.  
The database is accessed programmatically through the official **`psycopg2`** Python connector, which ensures encrypted and authenticated transactions between the data-collection script and the server.

Access to the database is restricted to authorized researchers and conducted exclusively over secure (SSL/SSH) connections.  
No raw message data are redistributed publicly, in full compliance with Telegram’s Terms of Service and institutional data-protection requirements.


---

## 7. Legal and Institutional Alignment
This data-collection process fully complies with:
- **Telegram’s [Terms of Service](https://telegram.org/tos)** and official API usage guidelines, including restrictions on unauthorized scraping and redistribution;  
- **U.S. fair-use principles** governing the use of publicly available online content for scholarly research and non-commercial purposes.


---

**Summary:**  
All data were collected through authorized Telegram API endpoints, limited to publicly available channels and textual content.  
The project does not access private communications or personal user data, and it operates entirely within Telegram’s technical and legal Terms of Service.
