from openai import AsyncOpenAI
import json
from app.core.config import SYSTEM_PROMPT_SUM, OPENAI_API_KEY, REWRITE_SYSTEM_PROMPT

class ChatHistory:
    def __init__(self):
        self.last_recommended_ids: list[str] = []

    @staticmethod
    async def summarize_history(messages):
        summary_prompt = "Summarize the following conversation: " + str(messages)
        summary_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        response = await summary_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SUM},
                {"role": "user", "content": summary_prompt}
            ]
        )

        return response.choices[0].message.content
    
    async def rewrite_query(self, history_messages, user_query):
        rewrite_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        rewrite_messages = history_messages + [
            {"role": "user", "content": user_query}
        ]

        rewrite_system_prompt = REWRITE_SYSTEM_PROMPT

        response = await rewrite_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": rewrite_system_prompt},
                *rewrite_messages
            ],
            temperature=0.0
        )
        
        raw_response = response.choices[0].message.content.strip()
        
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            print("DEBUG: JSON-ERROR: Fallback is in use!")
            data = {
                "normalized_query": user_query,
                "intent": "other",
                "aspects": ["other"],
                "tea_name": None,
                "tea_id": None,
            }
        
        # Intent validation
        valid_intents = {"price", "caffeine", "ingredients", "recommendation", "comparison", "cross_sell", "other"}
        intent = data.get("intent", "other")
        
        if intent not in valid_intents:
            intent = "other"
        
        data["intent"] = intent
        
        # Aspect validation
        raw_aspects = data.get("aspects", [])
        
        if isinstance(raw_aspects, str):
            aspects = [raw_aspects]
        elif isinstance(raw_aspects, list):
            aspects = [a for a in raw_aspects if a in valid_intents and a != "other"]
        else:
            aspects = []

        if not aspects:
            aspects = [intent]
        data["aspects"] = aspects

        # Request_type validation
        valid_request_types = {"herbal", "black", "green", "fruit"}
        request_type = data.get("request_type")

        if request_type not in valid_request_types:
            request_type = None
        
        data["request_type"] = request_type

        # Ingredient validation
        request_ingredients = data.get("request_ingredients")

        if not isinstance(request_ingredients, list):
            request_ingredients = []
        
        data["request_ingredients"] = [
            ing.lower() for ing in request_ingredients if isinstance(ing, str) and ing.strip()
        ]

        # Target_scope validation
        target_scope = data.get("target_scope")
        valid_scopes = {"single", "all_recommended"}

        if target_scope not in valid_scopes:
            target_scope = "single"
        
        data["target_scope"] = target_scope

        # Cross_sell validation
        cross_sell_target = data.get("cross_sell_target")
        valid_cross_sell_targets = {"last_recommended", "named_product", "generic"}

        if cross_sell_target not in valid_cross_sell_targets:
            cross_sell_target = None
        
        data["cross_sell_target"] = cross_sell_target

        # Use_case validation
        raw_use_cases = data.get("use_cases", [])

        if isinstance(raw_use_cases, str):
            use_cases = [raw_use_cases]
        elif isinstance(raw_use_cases, list):
            use_cases = [u.strip().lower() for u in raw_use_cases if isinstance(u, str) and u.strip()]
        else:
            use_cases = []

        data["use_cases"] = use_cases

        # recipient_type validation
        recipient_type = data.get("recipient_type")
        if not isinstance(recipient_type, str) or not recipient_type.strip():
            recipient_type = None
        else:
            recipient_type = recipient_type.strip().lower()

        data["recipient_type"] = recipient_type

        # Budget validation
        def _to_float(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
            
        budget_min = _to_float(data.get("budget_min"))
        budget_max = _to_float(data.get("budget_max"))

        if budget_min is not None and budget_max is not None:
            if budget_min > budget_max:
                budget_min, budget_max = budget_max, budget_min

        data["budget_min"] = budget_min
        data["budget_max"] = budget_max

        # safety_topic validation
        safety_topic = data.get("safety_topic")
        valid_safety_topics = {None, "none", "health"}

        if safety_topic not in valid_safety_topics:
            safety_topic = None
        
        data["safety_topic"] = safety_topic

        return data
    
    def remember_recommendation(self, tea_ids: list[str]) -> None:
        self.last_recommended_ids = list(tea_ids)
        print("DEBUG: remember_recommendation ->", self.last_recommended_ids)

    def get_last_recommendation(self) -> list[str]:
        return self.last_recommended_ids