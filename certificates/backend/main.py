import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "participants.csv")
TEMPLATE_FILE = os.path.join(BASE_DIR, "certificate_template.png")

# ✅ Load data
df = pd.read_csv(CSV_FILE)
df["Name"] = df["Name"].astype(str).str.strip().str.lower()
name_set = set(df["Name"])

# ✅ Load template and RESIZE for memory efficiency
template_image = Image.open(TEMPLATE_FILE)
max_width = 1200
if template_image.width > max_width:
    ratio = max_width / template_image.width
    new_height = int(template_image.height * ratio)
    template_image = template_image.resize((max_width, new_height), Image.LANCZOS)

print(f"Template resized to: {template_image.size}")


# 🔍 SEARCH
@app.get("/search")
def search(name: str):
    clean_name = name.strip().lower()

    if clean_name in name_set:
        return {"Name": clean_name.title()}

    matches = [n for n in name_set if clean_name in n]

    if not matches:
        raise HTTPException(status_code=404, detail="Name not found.")

    return {"Name": matches[0].title()}


# 🎓 CERTIFICATE GENERATION
@app.get("/certificate")
def generate_certificate(name: str):
    clean_name = name.strip().lower()

    if clean_name not in name_set:
        raise HTTPException(status_code=404, detail="Name not found.")

    final_name = clean_name.title()

    try:
        image = template_image.copy()
        draw = ImageDraw.Draw(image)

        width, height = image.size
        print(f"Generating certificate for '{final_name}' - Image size: {width}x{height}")

        # 🔥 Fit the name to the certificate area and keep it above the description
        def load_font(size):
            try:
                return ImageFont.truetype("arial.ttf", size)
            except Exception:
                try:
                    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
                except Exception:
                    return ImageFont.load_default()

        font_size = 84
        font = load_font(font_size)
        max_text_width = int(width * 0.62)
        max_text_height = int(height * 0.10)

        while font_size > 18:
            bbox = draw.textbbox((0, 0), final_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            if text_width <= max_text_width and text_height <= max_text_height:
                break
            font_size -= 2
            font = load_font(font_size)

        bbox = draw.textbbox((0, 0), final_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) / 2
        # ✅ Final placement: below the certificate header line and above the description
        y = int(height * 0.42)

        print(f"Font size: {font_size}pt for '{final_name}' ({len(final_name)} chars)")
        print(f"Drawing at position ({int(x)}, {y})")

        draw.text((x, y), final_name, fill="black", font=font)

        # Save as JPEG
        img_io = io.BytesIO()
        image = image.convert("RGB")
        image.save(img_io, format="JPEG", quality=85)
        img_io.seek(0)

        print(f"Certificate generated successfully")

        return StreamingResponse(
            img_io,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{final_name}_certificate.jpg"'
            }
        )

    except Exception as e:
        print(f"Certificate Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Certificate generation failed")