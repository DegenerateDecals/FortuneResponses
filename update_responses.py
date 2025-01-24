import requests
import json
import base64

# Groq API Configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"

# GitHub Configuration
GITHUB_REPO = "DegenerateDecals/FortuneResponses"  # Replace with your GitHub username/repo
GITHUB_TOKEN = "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"  # Replace with your personal access token
RAW_FILE_PATH = "responses.json"  # File to update in GitHub


def query_groq(name, keywords):
    """Send a request to the Groq API."""
    prompt = f"Generate a fortune for {name} based on these keywords: {', '.join(keywords)}."
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
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"


def push_to_github(content):
    """Update the responses.json file in the GitHub repository."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{RAW_FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    # Fetch the existing file's SHA (needed for updates)
    response = requests.get(url, headers=headers)
    sha = response.json().get("sha", "")
    
    # Prepare the payload
    payload = {
        "message": "Update fortune response",
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha,
    }
    requests.put(url, headers=headers, json=payload)


if __name__ == "__main__":
    # Example usage
    name = "Player123"
    keywords = ["success", "happiness", "adventure"]
    
    fortune = query_groq(name, keywords)
    print(f"Generated fortune: {fortune}")
    
    # Update responses.json on GitHub
    response_data = {"fortune": fortune}
    push_to_github(json.dumps(response_data))
