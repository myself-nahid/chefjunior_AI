from fastapi import APIRouter
import cloudinary
import time

router = APIRouter()

@router.post("/cloudinary-signature")
async def generate_signature():
    timestamp = int(time.time())

    signature = cloudinary.utils.api_sign_request(
        {"timestamp": timestamp},
        cloudinary.config().api_secret
    )

    return {
        "timestamp": timestamp,
        "signature": signature,
        "api_key": cloudinary.config().api_key,
        "cloud_name": cloudinary.config().cloud_name,
    }