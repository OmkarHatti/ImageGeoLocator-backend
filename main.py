from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ExifTags
import io

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://image-geo-locate.vercel.app.",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Convert GPS
def convert_to_degrees(value):

    d = float(value[0])
    m = float(value[1])
    s = float(value[2])

    return d + (m / 60.0) + (s / 3600.0)


# Extract metadata
def extract_metadata(image):

    metadata = {}

    exif = image._getexif()

    if not exif:
        return metadata

    gps_info = {}

    for tag, value in exif.items():

        tag_name = ExifTags.TAGS.get(tag, tag)

        # Date & Time
        if tag_name == "DateTime":
            metadata["date_time"] = value

        # Camera Make
        if tag_name == "Make":
            metadata["camera_make"] = value

        # Camera Model
        if tag_name == "Model":
            metadata["camera_model"] = value

        # GPS
        if tag_name == "GPSInfo":

            for key in value.keys():

                gps_tag = ExifTags.GPSTAGS.get(key, key)

                gps_info[gps_tag] = value[key]

    # Latitude
    lat = gps_info.get("GPSLatitude")
    lat_ref = gps_info.get("GPSLatitudeRef")

    # Longitude
    lon = gps_info.get("GPSLongitude")
    lon_ref = gps_info.get("GPSLongitudeRef")

    # ONLY IF GPS EXISTS
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
    return {"message": "Backend running"}