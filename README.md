# ASCII Lab

An interactive studio that turns images, video and a live webcam feed into ASCII art, with
real-time controls, five rendering modes, dithering and particle effects. The rendering engine is
written in Python (NumPy + OpenCV) and served by FastAPI.

**Live demo:** https://ascii-lab.onrender.com/ (on the free tier it may take ~30 s to wake up)

![ASCII Lab landing page](docs/screenshots/landing.png)

## Features

- **Image to ASCII**: upload a JPG, PNG or WebP and convert it with live controls
- **Video to ASCII**: upload an MP4, WebM or MOV and play it back as an ASCII animation
- **Webcam to ASCII**: renders the camera feed as ASCII in real time
- **5 rendering modes**: Density, Blocks, Binary, Edge (OpenCV) and Custom
- **7 character sets**: Standard, Dense, Minimal, Blocks, Binary, Terminal and Edge
- **Image adjustments**: brightness, contrast, gamma and invert
- **3 dithering algorithms**: Floyd-Steinberg, Atkinson and ordered dithering
- **Color ASCII**: keeps the original color of each character's region
- **5 interactive effects**: Gravity, Vortex, Ripple, Explosion and Fire
- **Export**: copy to the clipboard or download as `.txt`

## How it works

```
upload / frame ─► resize ─┬─► grayscale ─► contrast/gamma ─► dithering ─┬─► char mapping ─► renderer
                          └─► edge detection (OpenCV, "edge" mode) ─────┘
           color modes: per-character color is sampled from the resized image before grayscale
```

| Module | Responsibility |
|---|---|
| `app/engine/` | The processing pipeline: resize, grayscale, contrast, dithering, edge detection, character mapping, color and rendering |
| `app/effects/` | Particle-style effects (gravity, vortex, ripple, explosion, fire) |
| `app/media/video.py` | Frame extraction and per-frame rendering for video |
| `app/api/` | REST endpoints (see below) |
| `frontend/` | A single-page UI in vanilla JS that talks to the API |
| `tests/` | pytest suites for the API, dithering, mapping, renderer and video |

### API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/render/image` | Render an uploaded image |
| `POST` | `/render/video` | Render an uploaded video |
| `POST` | `/render/video/frames` | Render video frames for playback |
| `POST` | `/render/webcam` | Render a single webcam frame |
| `GET` | `/render/modes` | List the rendering modes |
| `GET` | `/charsets` | List the character sets |
| `GET` | `/health` | Health check |

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
pytest                             # run the test suite
```

Or with Docker (this is how the Render deployment runs):

```bash
docker build -t ascii-lab .
docker run -p 8000:8000 ascii-lab
```

## Stack

Python · FastAPI · NumPy · OpenCV · Pillow · pytest · vanilla JS · Docker · Render
