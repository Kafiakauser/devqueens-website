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

# ✅ Load template ONCE and cache it
try:
    template_image = Image.open(TEMPLATE_FILE)
    print(f"Template loaded: {template_image.size} pixels")
except Exception as e:
    print(f"Error loading template: {e}")
    template_image = None


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
    if template_image is None:
        raise HTTPException(status_code=500, detail="Certificate template not found.")

    clean_name = name.strip().lower()

    if clean_name not in name_set:
        raise HTTPException(status_code=404, detail="Name not found.")

    final_name = clean_name.title()

    try:
        # ✅ SAFE: Resize template only once for processing
        image = template_image.copy()
        
        # Get image dimensions
        width, height = image.size
        print(f"Processing certificate for '{final_name}' - Image size: {width}x{height}")

        # 🔥 Smart font sizing based on actual image dimensions
        def get_font_size(name, img_width):
            # Scale font based on image width
            length = len(name)
            base_size = img_width / 6  # Use image width as reference
            
            if length <= 4:
                return int(base_size)
            elif length <= 6:
                return int(base_size * 0.95)
            elif length <= 8:
                return int(base_size * 0.90)
            elif length <= 10:
                return int(base_size * 0.85)
            elif length <= 12:
                return int(base_size * 0.80)
            elif length <= 14:
                return int(base_size * 0.75)
            elif length <= 16:
                return int(base_size * 0.70)
            elif length <= 18:
                return int(base_size * 0.60)
            else:
                return int(base_size * 0.50)

        font_size = get_font_size(final_name, width)
        print(f"Font size calculated: {font_size}pt for '{final_name}' ({len(final_name)} chars)")

        # ✅ Load font with fallback
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # Draw text
        draw = ImageDraw.Draw(image)

        # Calculate text dimensions
        bbox = draw.textbbox((0, 0), final_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center horizontally
        x = (width - text_width) / 2

        # Position at 40% from top (between "PRESENTED TO" and signature line)
        y = int(height * 0.38)

        print(f"Drawing text at position ({int(x)}, {y})")

        # Draw text in dark green
        draw.text((x, y), final_name, fill=(50, 70, 50), font=font)

        # ✅ Convert and save as JPEG
        img_io = io.BytesIO()
        image = image.convert("RGB")
        image.save(img_io, format="JPEG", quality=85, optimize=True)
        img_io.seek(0)

        print(f"Certificate generated successfully for {final_name}")

        return StreamingResponse(
            img_io,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{final_name}_certificate.jpg"'
            }
        )

    except Exception as e:
        print(f"Certificate Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Certificate generation failed: {str(e)}")