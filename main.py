from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ExifTags
import io

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://image-geo-locator-frontend.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Convert GPS coordinates
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


# Extract Metadata
def extract_metadata(image):

    exif_data = image.getexif()

    if not exif_data:
        return {}

    metadata = {}
    gps_info = {}

    for tag_id, value in exif_data.items():

        tag_name = ExifTags.TAGS.get(tag_id, tag_id)

        # Date & Time
        if tag_name == "DateTime":
            metadata["date_time"] = value

        # Camera Brand
        if tag_name == "Make":
            metadata["camera_make"] = value

        # Camera Model
        if tag_name == "Model":
            metadata["camera_model"] = value

        # GPS Data
        if tag_name == "GPSInfo":

            # SAFETY CHECK
            if isinstance(value, dict):

                for key, val in value.items():
                    gps_tag = ExifTags.GPSTAGS.get(key, key)
                    gps_info[gps_tag] = val

    # Coordinates
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


# Upload API
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:

        # CHECK IMAGE TYPE
        if not file.content_type.startswith("image/"):
            return {
                "status": "error",
                "message": "Please upload a valid image"
            }

        contents = await file.read()

        image = Image.open(io.BytesIO(contents))

        metadata = extract_metadata(image)

        return {
            "status": "success",
            "data": metadata
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/")
def home():
    return {"message": "Backend running successfully"}