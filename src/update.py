import json
import requests
import dearpygui.dearpygui as dpg

def get_version_to_update(current_version):
    latest_version = get_latest_version()


    if compare_versions(current_version, latest_version) < 0:
        return latest_version
    return None

def get_latest_version():
    url = "https://api.github.com/repos/deskup1/tagliatello/commits"
    response = requests.get(url, timeout=5)
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
            
def dpg_changelog(parent, width=600):
    with open("CHANGELOG.md", "r") as f:
        changelog = f.read()

    changelog = changelog.split("\n## ")
    changelog = changelog[1:]

    is_first = True
    with dpg.group(parent=parent, width=width):
        for section in changelog:
            sub_sections = section.split("\n### ")
            title = sub_sections[0].strip()
            with dpg.collapsing_header(label=title, default_open=is_first):

                for sub_section in sub_sections[1:]:
                    lines = sub_section.split("\n")
                    lines = [line for line in lines if line.strip() != ""]
                    subtitle = lines[0].strip()

                    with dpg.tree_node(label=subtitle, default_open=True):
                        for line in lines[1:]:
                            if line.startswith("- "):
                                dpg.add_text(line[2:], bullet=True, wrap=width-60)
                            else:
                                dpg.add_text(line.strip(), wrap=width-40)

            is_first = False

    
if __name__ == "__main__":
    dpg.create_context()
    dpg.create_viewport(title="Tagliatello", width=800, height=600)
    with dpg.window(label="Changelog", width=800, height=600):
        dpg_changelog(dpg.last_item())
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()