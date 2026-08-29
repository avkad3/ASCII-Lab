# ASCII Lab

Python-based interactive ASCII rendering platform.

## Features

- **Image to ASCII** — Upload JPG/PNG/WebP and convert to ASCII with live controls
- **Video to ASCII** — Upload MP4/WebM/MOV and play back as ASCII animation
- **Webcam to ASCII** — Real-time camera feed rendered as ASCII art
- **5 Rendering Modes** — Density, Blocks, Binary, Edge (OpenCV), Custom
- **7 Character Sets** — Standard, Dense, Minimal, Blocks, Binary, Terminal, Edge
- **Image Adjustments** — Brightness, Contrast, Gamma, Invert
- **3 Dithering Algorithms** — Floyd-Steinberg, Atkinson, Ordered
- **Color ASCII** — Original color extraction per character
- **5 Interactive Effects** — Gravity, Vortex, Ripple, Explosion, Fire
- **Export** — Copy to clipboard or download as .txt

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
uvicorn app.main:app --reload

# 3. Open http://localhost:8000