from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

def get_best_format(url):
    """
    Returns best video+audio format for download.
    """
    ydl_opts = {"quiet": True, "dump_single_json": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])

        # Filter only formats with both video and audio
        video_audio_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") != "none"]

        # Sort by resolution and fps
        def quality_key(f):
            height = f.get("height") or 0
            fps = f.get("fps") or 0
            return (height, fps)

        if video_audio_formats:
            best = max(video_audio_formats, key=quality_key)
        else:
            # fallback if no combined formats, pick best video only
            best = max(formats, key=quality_key)

        return best

@app.route("/getFormats", methods=["POST"])
def get_formats():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        best = get_best_format(url)
        return jsonify({
            "title": best.get("title") or "Video",
            "format_id": best.get("format_id"),
            "ext": best.get("ext"),
            "resolution": f"{best.get('height')}p" if best.get("height") else "audio only",
            "vcodec": best.get("vcodec"),
            "acodec": best.get("acodec"),
            "filesize": best.get("filesize") or best.get("filesize_approx")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    format_id = data.get("format_id")

    if not url or not format_id:
        return jsonify({"error": "URL and format_id are required"}), 400

    try:
        ydl_opts = {
            "format": format_id,
            "outtmpl": "%(title)s.%(ext)s",  # saves as video_title.ext
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return jsonify({"message": "Download complete", "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
