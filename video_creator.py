import os
import requests
from moviepy.editor import *
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from fallbacks import generate_script, fetch_media_with_fallback

set_api_key(os.environ["ELEVENLABS_API_KEY"])

def create_voiceover(script: str, output_file: str = "audio.mp3") -> str:
    """Generate speech from script using ElevenLabs."""
    audio = generate(
        text=script,
        voice=Voice(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            settings=VoiceSettings(stability=0.3, similarity_boost=0.7)
        ),
        model="eleven_monolingual_v1"
    )
    with open(output_file, "wb") as f:
        f.write(audio)
    return output_file

def assemble_video(audio_path: str, media_path: str, output_video: str = "final.mp4") -> str:
    """Combine audio with video or image. Adjust duration for images."""
    if media_path.endswith((".mp4", ".webm", ".mov", ".avi")):
        clip = VideoFileClip(media_path)
    else:  # image
        # load image, set duration equal to audio length
        img_clip = ImageClip(media_path)
        audio_clip = AudioFileClip(audio_path)
        clip = img_clip.set_duration(audio_clip.duration).set_audio(audio_clip)
        clip = clip.resize(height=720)
        clip.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")
        return output_video
    # If video, trim/crop to audio length
    audio_clip = AudioFileClip(audio_path)
    if clip.duration > audio_clip.duration:
        clip = clip.subclip(0, audio_clip.duration)
    clip = clip.set_audio(audio_clip)
    clip = clip.resize(height=720)
    clip.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")
    return output_video

def generate_video_task(prompt: str, job_id: str) -> dict:
    """Full pipeline – returns dict with status or error."""
    try:
        # 1. Script
        script = generate_script(prompt)
        # 2. Extract simple keyword from prompt (first 3 words)
        keyword = " ".join(prompt.split()[:3])
        # 3. Media
        media_url = fetch_media_with_fallback(keyword)
        # download media
        ext = ".mp4" if "video" in media_url or ".mp4" in media_url else ".jpg"
        media_local = f"temp_{job_id}{ext}"
        with open(media_local, "wb") as f:
            f.write(requests.get(media_url).content)
        # 4. Voiceover
        audio_file = f"audio_{job_id}.mp3"
        create_voiceover(script, audio_file)
        # 5. Assemble video
        output_video = f"output_{job_id}.mp4"
        assemble_video(audio_file, media_local, output_video)
        # cleanup temp files (optional)
        return {"status": "completed", "video_path": output_video}
    except Exception as e:
        return {"status": "failed", "error": str(e)}