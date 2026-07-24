import os
from dotenv import load_dotenv

from main import publish_to_buffer

load_dotenv()

with open(
    "output/post_2026-07-24_17-21.txt",
    "r",
    encoding="utf-8",
) as f:
    post = f.read()

print("\nPOST TO PUBLISH:\n")
print(post)

confirm = input("\nPublish this to LinkedIn? (yes/no): ")

if confirm.lower() == "yes":
    result = publish_to_buffer(post)

    print("\n✅ Sent to Buffer")
    print(result)

else:
    print("\n❌ Cancelled")