import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    위도/경도를 기준으로 두 지점 사이의 거리(km)를 반환
    """
    R = 6371  # 지구 반지름 (km)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
