import os
import requests
import google.generativeai as genai
from error_handler import APIError, fallback

# ---------- SCRIPT GENERATION ----------
@fallback(default_value="No script could be generated. Please try again.")
def generate_script_deepseek(prompt: str) -> str:
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    resp = requests.post(url, json=data, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def generate_script_gemini(prompt: str) -> str:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def generate_script(prompt: str) -> str:
    """Primary: DeepSeek → Fallback: Gemini"""
    try:
        return generate_script_deepseek(prompt)
    except Exception as e:
        print(f"DeepSeek failed: {e}, switching to Gemini")
        return generate_script_gemini(prompt)

# ---------- MEDIA SEARCH ----------
def search_pixabay_media(keyword: str, media_type: str = "video") -> str:
    """Return URL of first result. Raises if none."""
    if media_type == "video":
        url = "https://pixabay.com/api/videos/"
        params = {"key": os.environ["PIXABAY_API_KEY"], "q": keyword, "per_page": 3}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", [])
        if hits:
            # pick largest video
            videos = hits[0]["videos"]
            for quality in ["large", "medium", "small"]:
                if quality in videos:
                    return videos[quality]["url"]
            return list(videos.values())[0]["url"]
    else:  # image
        url = "https://pixabay.com/api/"
        params = {"key": os.environ["PIXABAY_API_KEY"], "q": keyword, "image_type": "photo", "per_page": 3}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", [])
        if hits:
            return hits[0]["webformatURL"]
    raise Exception("No media found for keyword: " + keyword)

def fetch_media_with_fallback(keyword: str) -> str:
    """Try video → image → placeholder."""
    try:
        return search_pixabay_media(keyword, "video")
    except:
        try:
            return search_pixabay_media(keyword, "image")
        except:
            return "https://pixabay.com/static/uploads/placeholder.png"