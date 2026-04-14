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

        # 🔥 Reasonable font sizing
        def get_font_size(name):
            length = len(name)
            if length <= 6:
                return 120
            elif length <= 10:
                return 100
            elif length <= 14:
                return 85
            elif length <= 18:
                return 70
            else:
                return 55

        font_size = get_font_size(final_name)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Center text
        bbox = draw.textbbox((0, 0), final_name, font=font)
        text_width = bbox[2] - bbox[0]

        x = (width - text_width) / 2
        y = height * 0.40

        draw.text((x, y), final_name, fill="black", font=font)

        # Save as JPEG
        img_io = io.BytesIO()
        image = image.convert("RGB")
        image.save(img_io, format="JPEG", quality=80)
        img_io.seek(0)

        return StreamingResponse(
            img_io,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{final_name}_certificate.jpg"'
            }
        )

    except Exception as e:
        print("Certificate Error:", str(e))
        raise HTTPException(status_code=500, detail="Certificate generation failed")