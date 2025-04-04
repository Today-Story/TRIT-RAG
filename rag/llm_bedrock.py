import boto3
import json
import re
import random
from botocore.config import Config

# Claude 3 Haiku 모델 설정
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=Config(retries={"max_attempts": 3})
)

# Claude 3 Messages API 형식 호출
def invoke_claude(prompt: str) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response['body'].read().decode())
    return result["content"][0]["text"]


# 콘텐츠 또는 장소 중 하나 추천
def ask_llama_for_json(user, items, item_type="contents"):
    items = random.sample(items, min(len(items), 10))
    formatted_items = "".join(
        f"- ID: {item['id']}, Title: {item['title']}, Description: {item['desc']}\n"
        if item_type == "contents" else
        f"- ID: {item['id']}, Name: {item['title']}, Address: {item['desc']}\n"
        for item in items
    )

    prompt = f"""
You're a smart recommender.

User:
- Name: {user['name']}, Age: {user['age']}, Gender: {user['gender']}, Country: {user['country']}
- Category: {user['category']}, Needs: {user['needs']}
- Location: ({user['latitude']}, {user['longitude']})

Available {item_type}:
{formatted_items}

Pick the best-matching {item_type[:-1]} for this user. 
Respond only in JSON format:
{{
  "{item_type}Id": <ID>,
  "reason": "<3-line message (~120 characters), emotionally intuitive and behavior-based>"
}}
"""
    try:
        result = invoke_claude(prompt)
        match = re.search(r"\{[\s\S]*?\}", result)
        return json.loads(match.group(0)) if match else None
    except Exception as e:
        print("Claude JSON 응답 실패:", e)
        return None


# 장소 기반 감성 메시지 생성
def generate_reason_emotional(user, place_name, category, place_facts, keywords):
    keyword_str = ", ".join([f"**{k}**" for k in keywords])
    prompt = f"""
You’re a travel-savvy friend. Recommend a specific place emotionally.

Format:
- First line: short emotionally resonant title (< 60 characters)
- Then exactly 3 lines (< 120 characters total), in this format:
1. Personality decoding
2. Place decoding
3. Mood match + **keywords**: {keyword_str}

Place name: {place_name}
Category: {category}
Place insight:
{place_facts}

Return JSON like:
{{
  "title": "<short title>",
  "lines": ["<line1>", "<line2>", "<line3>"]
}}
"""
    try:
        result = invoke_claude(prompt)
        match = re.search(r"\{[\s\S]*?\}", result)
        return json.loads(match.group(0)) if match else None
    except Exception as e:
        print("Claude 메시지 실패:", e)
        return None
