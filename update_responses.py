import requests
import json
import base64
from flask import Flask, request, jsonify
from typing import List
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
#  Groq API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"

# ─────────────────────────────────────────────────────────────────────────────
#  GITHUB CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_USERNAME = "DegenerateDecals"
GITHUB_TOKEN = "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"
GITHUB_REPO = "FortuneResponses"
FILE_PATH = "responses.json"

# ─────────────────────────────────────────────────────────────────────────────
#  Flask Application Setup
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Query Groq for a New Fortune
# ─────────────────────────────────────────────────────────────────────────────
def query_groq(name: str, keywords: List[str]) -> str:
    """
    Generate a fortune from the Groq API using the provided 'name' and 'keywords'.
    """
    unique_timestamp = datetime.now(timezone.utc).isoformat()
    prompt = (
        f"Generate a fortune for {name} based on these keywords: {', '.join(keywords)}.\n"
        f"Add a unique timestamp: {unique_timestamp}."
    )
    payload = {
        "model": "llama-3.2-1b-preview",
        "messages": [
            {"role": "system", "content": "You are a fortune teller."},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        print(f"[DEBUG] Sending request to Groq API with unique timestamp: {unique_timestamp}")
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(f"[DEBUG] Received response from Groq API: {data}")

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            return "Error: Groq API returned an unexpected format."
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error connecting to Groq API: {e}")
        return f"Error connecting to Groq API: {e}"

# ─────────────────────────────────────────────────────────────────────────────
#  Update or Create responses.json on GitHub via REST API
# ─────────────────────────────────────────────────────────────────────────────
def update_github_file(new_content: str) -> None:
    """
    Create or update responses.json in your GitHub repo with 'new_content' (string).
    """
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN.strip()}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        print("[DEBUG] Checking if file exists on GitHub...")
        get_resp = requests.get(url, headers=headers)
        if get_resp.status_code == 401:
            print("[ERROR] Unauthorized: Check the GitHub token permissions or scope.")
            print(f"[DEBUG] Response: {get_resp.json()}")
            return

        get_resp.raise_for_status()

        if get_resp.status_code == 200:
            current_sha = get_resp.json().get("sha")
            print(f"[DEBUG] File exists. Updating content with SHA: {current_sha}")
            payload = {
                "message": "Update fortune response",
                "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
                "sha": current_sha
            }
        elif get_resp.status_code == 404:
            print("[DEBUG] File does not exist. Creating new file...")
            payload = {
                "message": "Create fortune response",
                "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            }
        else:
            print(f"[ERROR] Unexpected response while checking file existence: {get_resp.status_code}")
            return

        print("[DEBUG] Sending request to update/create file on GitHub...")
        put_resp = requests.put(url, headers=headers, json=payload)
        if put_resp.status_code == 401:
            print("[ERROR] Unauthorized: Invalid GitHub token or insufficient permissions.")
            print(f"[DEBUG] Response: {put_resp.json()}")
            return

        put_resp.raise_for_status()

        if put_resp.status_code in (200, 201):
            print("[DEBUG] File successfully created/updated on GitHub!")
        else:
            print(f"[ERROR] Unexpected response from GitHub: {put_resp.status_code} - {put_resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error communicating with GitHub: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  Flask Route to Handle Fortune Requests
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/generate_fortune', methods=['GET'])
def generate_fortune():
    """
    Flask route to handle fortune generation. Accepts 'name' and 'keywords' as query params.
    """
    name = request.args.get('name')
    keywords = request.args.getlist('keywords')

    if not name or not keywords:
        print("[ERROR] Missing 'name' or 'keywords' parameters.")
        return jsonify({"error": "Missing required parameters 'name' or 'keywords'."}), 400

    print(f"[DEBUG] Received request: name={name}, keywords={keywords}")

    fortune_text = query_groq(name, keywords)
    print(f"[DEBUG] Generated fortune: {fortune_text}")

    new_json_data = {
        "fortune": fortune_text,
        "name": name,
        "keywords": keywords
    }

    try:
        print("[DEBUG] Updating GitHub with new content...")
        update_github_file(json.dumps(new_json_data, indent=2))
    except Exception as e:
        print(f"[ERROR] Failed to update GitHub: {e}")
        return jsonify({"error": "Failed to update GitHub."}), 500

    return jsonify({"status": "success", "fortune": fortune_text}), 200

# ─────────────────────────────────────────────────────────────────────────────
#  Run Flask Application
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[INFO] Starting Flask server...")
    app.run(debug=True, host="0.0.0.0", port=5000)