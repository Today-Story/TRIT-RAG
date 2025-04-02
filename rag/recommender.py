from rag.utils import calculate_distance
from rag.llm_bedrock import ask_llama_for_json, generate_reason_emotional
from rag.websearch import search_web, summarize_place_facts, extract_top_keywords

def generate_recommendation(user, contents, locations, creators):
    needs = user["needs"].lower()

    if needs == "contents":
        matched_contents = [
            c for c in contents
            if c["category"].strip().upper() == user["category"].strip().upper()
        ]

        llama_result = ask_llama_for_json(user, matched_contents, "contents")

        if llama_result:
            recommended_content_id = llama_result.get("contentsId")
            recommended = next((c for c in matched_contents if c["id"] == recommended_content_id), None)

            # 웹 검색 기반 reason 생성
            if recommended:
                query = f"{recommended['title']} {user['category']} travel"
                web_results = search_web(query)
                place_facts = summarize_place_facts(web_results)
                keywords = extract_top_keywords(web_results)

                reason_result = generate_reason_emotional(
                    user=user,
                    place_name=recommended["title"],
                    category=recommended["category"],
                    place_facts=place_facts,
                    keywords=keywords
                )
            else:
                reason_result = None

            # 관련 장소 찾기
            related_locations = [loc for loc in locations if loc["contents_id"] == recommended_content_id]
            user_lat, user_lon = float(user["latitude"]), float(user["longitude"])

            nearest = min(
                related_locations,
                key=lambda loc: calculate_distance(user_lat, user_lon, loc["latitude"], loc["longitude"]),
                default=None
            )

            content_info = {
                "contentsId": recommended_content_id,
                "locationId": nearest["id"] if nearest else None,
                "latitude": nearest["latitude"] if nearest else None,
                "longitude": nearest["longitude"] if nearest else None,
                "googleMapId": nearest["google_map_id"] if nearest else None,
            } if nearest else None
        else:
            content_info = None
            reason_result = None

        return {
            "userId": user["userId"],
            "message": {
                "recommendation": {
                    "contentsId": content_info,
                    "locationId": None,
                    "creatorId": None,
                    "reason": (
                        reason_result if reason_result
                        else {"title": "Recommendation", "lines": [llama_result.get("reason")]} if llama_result
                        else {"title": "Recommendation", "lines": ["Could not generate content recommendation."]}
                    )
                }
            }
        }

    elif needs == "location":
        user_lat, user_lon = float(user["latitude"]), float(user["longitude"])
        category = user["category"].strip().upper()

        filtered_locations = [loc for loc in locations if loc.get("category", "").strip().upper() == category]
        nearest = None
        min_distance = float("inf")

        for loc in filtered_locations:
            dist = calculate_distance(user_lat, user_lon, loc["latitude"], loc["longitude"])
            if dist <= 80 and dist < min_distance:
                nearest, min_distance = loc, dist

        if nearest:
            reason = (
                f"We found a {category.lower()} spot just {min_distance:.2f} km away from you. "
                f"It suits your interest and is conveniently located based on your current position."
            )
            return {
                "userId": user["userId"],
                "message": {
                    "recommendation": {
                        "contentsId": None,
                        "locationId": {
                            "locationId": nearest["id"],
                            "latitude": nearest["latitude"],
                            "longitude": nearest["longitude"],
                            "googleMapId": nearest["google_map_id"]
                        },
                        "creatorId": None,
                        "reason": reason
                    }
                }
            }
        else:
            return {
                "userId": user["userId"],
                "message": {
                    "recommendation": {
                        "contentsId": None,
                        "locationId": None,
                        "creatorId": None,
                        "reason": f"Sorry, we couldn't find any suitable {category.lower()} places within 80 km of your location."
                    }
                }
            }

    elif needs == "creator":
        user_category = (user.get("category") or "").strip().upper()
        user_country = (user.get("country") or "").strip().upper()

        # 같은 category를 가진 creator
        creators_same_category = [
            c for c in creators
            if user_category in [cat.strip().upper() for cat in (c.get("category") or [])]
        ]

        # 둘 다 일치하는 creator 추천
        matched_creators = [
            c for c in creators_same_category
            if (c.get("country") or "").strip().upper() == user_country
        ]

        if matched_creators:
            selected = matched_creators[0]
            return {
                "userId": user["userId"],
                "message": {
                    "recommendation": {
                        "contentsId": None,
                        "locationId": None,
                        "creatorId": {
                            "creatorId": selected["id"],
                            "instruction": selected["introduction"],
                            "youtube": selected["youtube"]
                        },
                        "reason": "We found a creator who matches your interests and region."
                    }
                }
            }
        else:
            return {
                "userId": user["userId"],
                "message": {
                    "recommendation": {
                        "contentsId": None,
                        "locationId": None,
                        "creatorId": None,
                        "reason": "Sorry, we couldn't find a suitable creator based on your preferences."
                    }
                }
            }

    else:
        return {
            "userId": user["userId"],
            "message": {
                "recommendation": {
                    "contentsId": None,
                    "locationId": None,
                    "creatorId": None,
                    "reason": "Unknown needs type."
                }
            }
        }
