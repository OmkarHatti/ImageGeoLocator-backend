from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ExifTags
import io

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://image-geo-locator-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 📍 Convert GPS
def convert_to_degrees(value):
    def to_float(v):
        try:
            return float(v)
        except:
            return float(v.num) / float(v.den)

    d = to_float(value[0])
    m = to_float(value[1])
    s = to_float(value[2])

    return d + (m / 60.0) + (s / 3600.0)


# 🚀 Extract Metadata
def extract_metadata(image):
    exif_data = image._getexif()

    if not exif_data:
        return None

    metadata = {}

    gps_info = {}

    for tag, value in exif_data.items():
        tag_name = ExifTags.TAGS.get(tag, tag)

        # 📅 Date & Time
        if tag_name == "DateTime":
            metadata["date_time"] = value

        # 📱 Camera Brand
        if tag_name == "Make":
            metadata["camera_make"] = value

        # 📷 Camera Model
        if tag_name == "Model":
            metadata["camera_model"] = value

        # 🌍 GPS
        if tag_name == "GPSInfo":
            for key in value:
                gps_info[ExifTags.GPSTAGS.get(key)] = value[key]

    # GPS Processing
    lat = gps_info.get("GPSLatitude")
    lat_ref = gps_info.get("GPSLatitudeRef")

    lon = gps_info.get("GPSLongitude")
    lon_ref = gps_info.get("GPSLongitudeRef")

    if lat and lon:
        lat = convert_to_degrees(lat)
        lon = convert_to_degrees(lon)

        if lat_ref != "N":
            lat = -lat

        if lon_ref != "E":
            lon = -lon

        metadata["lat"] = lat
        metadata["lon"] = lon

    return metadata


# API
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()

    image = Image.open(io.BytesIO(contents))

    metadata = extract_metadata(image)

    if metadata:
        return {
            "status": "success",
            "data": metadata
        }

    return {
        "status": "error",
        "message": "No metadata found"
    }