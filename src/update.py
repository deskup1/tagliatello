import json
import requests

def get_version_to_update(current_version):
    latest_version = get_latest_version()


    if compare_versions(current_version, latest_version) < 0:
        return latest_version
    return None

def get_latest_version():
    url = "https://api.github.com/repos/deskup1/tagliatello/commits"
    response = requests.get(url)
    commits = json.loads(response.text)
    # find latest commit that  has message starting with "release:"

    for commit in commits:
        # if ends with -rc, skip
        if commit["commit"]["message"].endswith("-rc"):
            continue
        if commit["commit"]["message"].startswith("release:"):
            return commit["commit"]["message"].split(":")[1].strip()

if __name__ == "__main__":
    print(f"Latest version: {get_latest_version()}")


def parse_version(v):
    parts = v.split("-")
    version = parts[0]
    pre_release = None
    if len(parts) > 1:
        pre_release = parts[1]
    return version, pre_release

# version format: "vX.Y.Z"
def parse_version_number(v):
    return list(map(int, v[1:].split(".")))


# version format: "vX.Y.Z-(alpha|beta|rc)"
def compare_versions(v1, v2):
    v1_number, v1_pre_release = parse_version(v1)
    v2_number, v2_pre_release = parse_version(v2)

    if parse_version_number(v1_number) > parse_version_number(v2_number):
        return 1
    elif parse_version_number(v1_number) < parse_version_number(v2_number):
        return -1
    else:
        if v1_pre_release is None and v2_pre_release is not None:
            return 1
        elif v1_pre_release is not None and v2_pre_release is None:
            return -1
        elif v1_pre_release is None and v2_pre_release is None:
            return 0
        else:
            if v1_pre_release == "alpha" and v2_pre_release != "alpha":
                return -1
            elif v1_pre_release != "alpha" and v2_pre_release == "alpha":
                return 1
            elif v1_pre_release == "beta" and v2_pre_release != "beta":
                return -1
            elif v1_pre_release != "beta" and v2_pre_release == "beta":
                return 1
            elif v1_pre_release == "rc" and v2_pre_release != "rc":
                return -1
            elif v1_pre_release != "rc" and v2_pre_release == "rc":
                return 1
            else:
                return 0