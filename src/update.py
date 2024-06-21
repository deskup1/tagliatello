import json
import requests

def get_latest_version():
    url = "https://api.github.com/repos/deskup1/tagliatello/commits"
    response = requests.get(url)
    commits = json.loads(response.text)
    # find latest commit that  has message starting with "release:"

    for commit in commits:
        if commit["commit"]["message"].startswith("release:"):
            return commit["sha"]

if __name__ == "__main__":
    print(f"Latest version: {get_latest_version()}")