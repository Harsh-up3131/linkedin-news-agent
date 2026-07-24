import os
import requests
from dotenv import load_dotenv

load_dotenv()

BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_API_URL = "https://api.buffer.com"

headers = {
    "Authorization": f"Bearer {BUFFER_API_KEY}",
    "Content-Type": "application/json",
}


def graphql(query):
    response = requests.post(
        BUFFER_API_URL,
        headers=headers,
        json={"query": query},
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


# ----------------------------------
# Get organizations
# ----------------------------------

org_data = graphql("""
query {
    account {
        organizations {
            id
            name
        }
    }
}
""")

organizations = org_data["account"]["organizations"]

print("\nOrganizations:")

for org in organizations:
    print(f"- {org['name']}: {org['id']}")


# ----------------------------------
# Get connected channels
# ----------------------------------

for org in organizations:

    org_id = org["id"]

    channel_data = graphql(f"""
    query {{
        channels(
            input: {{
                organizationId: "{org_id}"
            }}
        ) {{
            id
            name
            displayName
            service
        }}
    }}
    """)

    print(f"\nChannels in {org['name']}:")

    for channel in channel_data["channels"]:
        print(
            f"- {channel['service']} | "
            f"{channel['displayName']} | "
            f"{channel['id']}"
        )