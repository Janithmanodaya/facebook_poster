import os
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.utils.collage import make_3x3_collage


# App setup
app = FastAPI(title="Ganudenu.store Vehicle Ad API")

# CORS for public connectivity (adjust origins if you want to restrict)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "..", "uploads")
GENERATED_DIR = os.path.join(BASE_DIR, "..", "generated")
COLLAGES_DIR = os.path.join(GENERATED_DIR, "collages")

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(COLLAGES_DIR, exist_ok=True)

# Jinja environment
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"])
)

# Static serving for generated files
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# Optional API key protection via header
# If you want a fixed API key regardless of environment, set it here.
# NOTE: This overrides the environment variable.
FIXED_API_KEY = "a3b7f219-47c9-4e01-b9d3-6b72d1b4e8c2"
API_KEY = (FIXED_API_KEY or os.getenv("API_KEY", "").strip())

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    # If API_KEY is configured, require header match
    if API_KEY and (x_api_key or "") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")
    return True


@app.get("/", response_class=HTMLResponse)
def root():
    # Render client UI
    template = env.get_template("ui.html")
    return template.render(site_name="Ganudenu.store")


@app.get("/api/collage/{filename}")
def get_collage(filename: str):
    """
    Download endpoint for generated collage image by filename.
    """
    path = os.path.join(COLLAGES_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Collage not found")
    return FileResponse(path, media_type="image/jpeg", filename=filename)


@app.post("/api/ads")
async def create_ad(
    verify: bool = Depends(verify_api_key),
    model: str = Form(...),
    manufacture_year: str = Form(...),
    price: str = Form(...),
    location: str = Form(...),
    price_type: str = Form(...),  # "Negotiable" or "Fixed"
    phone: str = Form(...),
    condition: str = Form(...),
    images: List[UploadFile] = File(...),  # 3-5 images recommended
):
    """
    Accepts ad details and images, generates a 3x3 collage, and renders 10 different HTML designs.
    Returns URLs to generated HTML files and the collage image.
    """
    # Basic validation
    if len(images) < 3:
        raise HTTPException(status_code=400, detail="Please upload at least 3 images.")
    if len(images) > 9:
        raise HTTPException(status_code=400, detail="Please upload a maximum of 9 images.")

    ad_id = str(uuid.uuid4())
    ad_upload_dir = os.path.join(UPLOADS_DIR, ad_id)
    ad_generated_dir = os.path.join(GENERATED_DIR, "ads", ad_id)
    os.makedirs(ad_upload_dir, exist_ok=True)
    os.makedirs(ad_generated_dir, exist_ok=True)

    # Save images
    saved_image_paths = []
    for idx, file in enumerate(images):
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            # default to .jpg if unknown
            ext = ".jpg"
        target_path = os.path.join(ad_upload_dir, f"img_{idx+1}{ext}")
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
        saved_image_paths.append(target_path)

    # Generate collage (1080x1080 3x3)
    collage_filename = f"{ad_id}.jpg"
    collage_path = os.path.join(COLLAGES_DIR, collage_filename)
    make_3x3_collage(saved_image_paths, collage_path, size=(1080, 1080))

    # Prepare context
    context = {
        "site_name": "Ganudenu.store",
        "model": model,
        "manufacture_year": manufacture_year,
        "price": price,
        "location": location,
        "price_type": price_type,
        "phone": phone,
        "condition": condition,
        "images": [
            f"/generated_relative/{os.path.relpath(p, GENERATED_DIR)}"
            for p in saved_image_paths
        ],  # placeholder, we will adjust below
    }

    # For templates, we want URLs the browser can fetch. As uploads are outside /generated,
    # we will expose a relative path via a secondary mount if needed. For simplicity, copy
    # images into ad_generated_dir for serving.
    served_images = []
    for p in saved_image_paths:
        filename = os.path.basename(p)
        served_path = os.path.join(ad_generated_dir, filename)
        # copy file
        with open(p, "rb") as rf, open(served_path, "wb") as wf:
            wf.write(rf.read())
        served_images.append(f"/generated/ads/{ad_id}/{filename}")

    context["images"] = served_images
    collage_url = f"/generated/collages/{collage_filename}"
    collage_download_url = f"/api/collage/{collage_filename}"

    # Render and save 10 templates
    template_files = [
        "template1.html",
        "template2.html",
        "template3.html",
        "template4.html",
        "template5.html",
        "template6.html",
        "template7.html",
        "template8.html",
        "template9.html",
        "template10.html",
    ]

    generated_pages = []
    for tpl in template_files:
        template = env.get_template(tpl)
        html_str = template.render(**context)
        out_path = os.path.join(ad_generated_dir, tpl)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_str)
        generated_pages.append(f"/generated/ads/{ad_id}/{tpl}")

    return JSONResponse(
        {
            "ad_id": ad_id,
            "collage_url": collage_url,
            "collage_download_url": collage_download_url,
            "pages": generated_pages,
            "image_urls": served_images,
        }
    )