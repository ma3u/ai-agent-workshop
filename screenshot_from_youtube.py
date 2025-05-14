import re
import os
import subprocess
from urllib.parse import urlparse, parse_qs

# Path to your markdown summary
SUMMARY_MD = "AI-Agent-Lectures-Expert-Summary.md"
# Output directory for screenshots
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

YOUTUBE_LINK_RE = re.compile(r'\[([^\]]+)\]\((https://www\.youtube\.com/watch\?v=[^\)\s]+)(?:[&\?]t=(\d+))?\)')

def extract_links_with_line_numbers(md_path):
    links = []  # (title, url, timestamp, line_number)
    with open(md_path, "r") as f:
        for idx, line in enumerate(f):
            match = YOUTUBE_LINK_RE.search(line)
            if match:
                title = match.group(1)
                url = match.group(2)
                t = match.group(3)
                print(f"Found link: {url} at timestamp: {t if t else 0}")
                links.append((title, url, int(t) if t else 0, idx))
    return links

def download_and_screenshot(title, url, timestamp, screenshot_dir):
    import shutil
    # Check yt-dlp and ffmpeg availability
    if not shutil.which('yt-dlp'):
        print('ERROR: yt-dlp is not installed or not in PATH.')
        return
    if not shutil.which('ffmpeg'):
        print('ERROR: ffmpeg is not installed or not in PATH.')
        return
    # Prepare .videos folder
    videos_dir = '.videos'
    os.makedirs(videos_dir, exist_ok=True)
    video_id = parse_qs(urlparse(url).query)['v'][0]
    video_file = os.path.join(videos_dir, f"{video_id}.mp4")
    if not os.path.exists(video_file):
        print(f"Downloading video: {url} -> {video_file}")
        try:
            result = subprocess.run(["yt-dlp", "-f", "mp4", "-o", video_file, url], check=True, capture_output=True, text=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: yt-dlp failed: {e.stderr}")
            return
    else:
        print(f"Video already exists: {video_file}")
    # Calculate screenshot time (timestamp + 10s)
    shot_time = timestamp + 10
    filename = f"{title.lower().replace(' ', '_').replace('/', '_')}_{shot_time}s.png"
    out_path = os.path.join(screenshot_dir, filename)
    print(f"Taking screenshot at {shot_time}s: {out_path}")
    try:
        result = subprocess.run([
            "ffmpeg", "-ss", str(shot_time), "-i", video_file, "-frames:v", "1", out_path, "-y"
        ], check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"Saved screenshot: {out_path}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: ffmpeg failed: {e.stderr}")
        return

def screenshot_filename(video_id, timestamp):
    return f"{video_id}_{timestamp}s.png"

def insert_screenshot_refs(md_path, links):
    with open(md_path, "r") as f:
        lines = f.readlines()
    new_lines = []
    skip_next = False
    for idx, line in enumerate(lines):
        new_lines.append(line)
        if skip_next:
            skip_next = False
            continue
        match = re.search(r'\[([^\]]+)\]\((https://www\\.youtube\\.com/watch\\?v=[^\)\s]+)(?:\\?t=(\\d+))?\)', line)
        if match:
            url = match.group(2)
            t = match.group(3)
            video_id = parse_qs(urlparse(url).query)['v'][0]
            timestamp = int(t) if t else 0
            img_name = screenshot_filename(video_id, timestamp)
            img_path = f"./screenshots/{img_name}"
            # Check if next line is already the image reference
            if idx+1 < len(lines) and img_path in lines[idx+1]:
                continue  # Already present
            new_lines.append(f"![Screenshot]({img_path})\n")
            skip_next = False
    with open(md_path, "w") as f:
        f.writelines(new_lines)

def main():
    links = extract_links_with_line_numbers(SUMMARY_MD)
    for title, url, t, _ in links:
        try:
            video_id = parse_qs(urlparse(url).query)['v'][0]
            img_name = screenshot_filename(video_id, t)
            out_path = os.path.join(SCREENSHOT_DIR, img_name)
            if not os.path.exists(out_path):
                download_and_screenshot(title, url, t, SCREENSHOT_DIR)
        except Exception as e:
            print(f"Failed for {title}: {e}")
    insert_screenshot_refs(SUMMARY_MD, links)

if __name__ == "__main__":
    main()
