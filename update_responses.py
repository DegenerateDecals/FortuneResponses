def update_github_file(new_content):
    """
    Create or update responses.json in your GitHub repo with 'new_content' (string).
    Uses token-based Auth with your GitHub username + personal token.
    """
    # Prepare the authorization header
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # The endpoint for the specific file in your repo
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"

    try:
        # 1) Attempt to get the current file's SHA
        print("Fetching file information from GitHub...")
        get_resp = requests.get(url, headers=headers)

        if get_resp.status_code == 200:
            # File exists, extract the current SHA
            current_sha = get_resp.json()["sha"]
            print(f"File exists. Current SHA: {current_sha}")

            # Prepare payload to update existing file
            payload = {
                "message": "Update fortune response",
                "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
                "sha": current_sha
            }
        elif get_resp.status_code == 404:
            # File does not exist -> create it
            print("File does not exist. Creating a new file.")
            payload = {
                "message": "Create fortune response",
                "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            }
        else:
            # Some other error
            print(f"Error fetching file info: {get_resp.status_code} - {get_resp.text}")
            return

        # 2) PUT request to update or create the file
        print("Attempting to update/create the file on GitHub...")
        put_resp = requests.put(url, headers=headers, json=payload)
        if put_resp.status_code in (200, 201):
            print("File successfully created/updated on GitHub!")
        else:
            print(f"Error updating/creating file: {put_resp.status_code} - {put_resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"Exception during GitHub API call: {e}")
