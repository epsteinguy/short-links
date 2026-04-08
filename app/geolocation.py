import httpx
from typing import Optional

GEOLOCATION_API = "https://ip-api.com/json/{ip}"

async def get_location_from_ip(ip: str) -> dict:
    """
    Fetch geolocation data for an ip address.
    Returns dict with country and more data.
    Gets lat and lon of an user.
    """
    if ip in ("127.0.0.1", "::1", "localhost") or ip.startswith(("192.168.", "10.", "172.")):
        return{
            "country": "Local",
            "city": "Localhost",
            "status": "success"
        }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get (GEOLOCATION_API.format(ip=ip))
            data = response.json()

            if data.get("status") == "success":
                return{
                    "country": data.get("country", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "region": data.get("regionName", "Unknown"),
                    "isp": data.get("isp", "Unknown"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                }
            else: 
                return {"country": "Unknown", "city": "Unknown"}
        
    except Exception as e:
        print(f"Geolocation error: {e}")
        return {"country": "Unknown", "city": "Unknown"}
    
def get_client_ip(request) -> str:
    """
    Extract the real IP address
    Handles X-Forwarded for proxies/load balancers.
    """

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "Unknown"