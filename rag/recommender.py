from rag.utils import calculate_distance
from rag.llm_bedrock import ask_llama_for_json, generate_reason_emotional, generate_creator_reason
from rag.websearch import search_web, summarize_place_facts, extract_top_keywords
from rag.user_behavior import fetch_user_behavior_text
from rag.embedding_utils import get_embedding
from rag.pinecone_client import query_similar_users


def generate_recommendation(user, contents, locations, creators):
    needs = user["needs"].lower()

    # 사용자 행동 임베딩 생성 및 유사 사용자 검색
    user_behavior_text = fetch_user_behavior_text(user["userId"])
    user_embedding = get_embedding(user_behavior_text) if user_behavior_text else None

    similar_user_metadata = []
    if user_embedding:
        similar_user_results = query_similar_users(user_embedding, top_k=5)
        similar_user_metadata = [match["metadata"] for match in similar_user_results.matches if match.get("metadata")]

    if needs == "contents":
        matched_contents = [
            c for c in contents
            if c["category"].strip().upper() == user["category"].strip().upper()
        ]

        # 콘텐츠 없을 경우
        if not matched_contents:
            return {
                "userId": user["userId"],
                "message": {
                    "recommendation": {
                        "contentsId": None,
                        "creatorId": None,
                        "reason": {
                            "title": "No recommendation",
                            "lines": [f"There is no {user['category']} content available for you at the moment."]
                        }
                    }
                }
            }

        # 유사 사용자들이 선호한 콘텐츠 우선순위 반영
        preferred_content_ids = []
        for meta in similar_user_metadata:
            preferred_content_ids.extend(meta.get("preferred_content_ids", []))

        sorted_contents = sorted(
            matched_contents,
            key=lambda c: preferred_content_ids.index(str(c["id"])) if str(c["id"]) in preferred_content_ids else len(preferred_content_ids)
        ) if preferred_content_ids else matched_contents

        llama_result = ask_llama_for_json(user, sorted_contents, "contents")

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
                    "creatorId": None,
                    "reason": (
                        reason_result if reason_result
                        else {"title": "Recommendation", "lines": [llama_result.get("reason")]} if llama_result
                        else {"title": "Recommendation", "lines": ["Could not generate content recommendation."]}
                    )
                }
            }
        }

    elif needs == "creator":
        user_category = (user.get("category") or "").strip().upper()
        user_country = (user.get("country") or "").strip().upper()

        creators_same_category = [
            c for c in creators
            if user_category in [cat.strip().upper() for cat in (c.get("category") or [])]
        ]

        matched_creators = [
            c for c in creators_same_category
            if (c.get("country") or "").strip().upper() == user_country
        ]

        # 유사 사용자들의 선호 크리에이터 우선 반영
        preferred_creator_ids = []
        for meta in similar_user_metadata:
            preferred_creator_ids.extend(meta.get("preferred_creator_ids", []))

        sorted_creators = sorted(
            matched_creators,
            key=lambda c: preferred_creator_ids.index(str(c["id"])) if str(c["id"]) in preferred_creator_ids else len(preferred_creator_ids)
        ) if preferred_creator_ids else matched_creators

        # 크리에이터 없을 경우
        if not sorted_creators:
            return {
                "userId": user["userId"],
                "message": {
                    "recommendation": {
                        "contentsId": None,
                        "creatorId": None,
                        "reason": {
                            "title": "No creator found",
                            "lines": [f"No creators match your category and country."]
                        }
                    }
                }
            }

        selected = sorted_creators[0]
        reason = generate_creator_reason(user, selected)

        return {
            "userId": user["userId"],
            "message": {
                "recommendation": {
                    "contentsId": None,
                    "creatorId": {
                        "creatorId": selected["id"],
                        "instruction": selected["introduction"],
                        "youtube": selected["youtube"]
                    },
                    "reason": reason if reason else {
                        "title": "Matched Creator",
                        "lines": ["A creator matching your interest has been selected."]
                    }
                }
            }
        }

    else:
        return {
            "userId": user["userId"],
            "message": {
                "recommendation": {
                    "contentsId": None,
                    "creatorId": None,
                    "reason": "Unknown needs type."
                }
            }
        }
