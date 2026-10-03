from openai import AsyncOpenAI
from typing import Optional, Any

from app.services.prompt_creation import PromptCreation
from app.data.tea_repository import TeaRepository
from app.services.chat_history import ChatHistory
from app.services.prompt_factory import PromptFactory
from app.services.filter_logic import FilterController
from app.core.config import ASPECT_FIELD_MAP

class IntentResponder:
    def __init__(self, chat_client: AsyncOpenAI, system_prompt: str, tea_repo: TeaRepository, chat_history: ChatHistory, prompt_factory: PromptFactory):
        self.chat_client = chat_client
        self.system_prompt = system_prompt
        self.tea_repo = tea_repo
        self.chat_history = chat_history
        self.prompt_factory = prompt_factory

    async def respond(self, intent: str, tea_info: Optional[dict[str, Any]], rewritten_data: dict[str, Any], results, history_messages: list[dict]) -> str:
        raw_aspects = rewritten_data.get("aspects") or []
        if isinstance(raw_aspects, str):
            aspects = {raw_aspects}
        else:
            aspects = set(raw_aspects)

        simple_aspects = {"price", "ingredients", "caffeine"}
        num_simple = len(aspects & simple_aspects)
        
        if intent not in {"price", "caffeine", "ingredients", "recommendation", "comparison", "cross_sell", "other"}:
            intent = "other"
        
        if intent == "cross_sell":
            use_cases = rewritten_data.get("use_cases", [])
            use_cases = [u.lower() for u in use_cases if isinstance(u, str)]
            if "gift" in use_cases:
                return await self.respond_gift_recommendation(tea_info, rewritten_data, results, history_messages)
            else:
                return await self.respond_cross_sell(tea_info, rewritten_data, results, history_messages)

        if intent == "recommendation" or "recommendation" in aspects:
            return await self.respond_recommendation(tea_info, rewritten_data, results, history_messages)
        
        if intent == "comparison" or "comparison" in aspects:
            return await self.respond_comparison(tea_info, rewritten_data, results, history_messages)
        
        if num_simple > 1:
            return await self.respond_multi(tea_info, rewritten_data, results, history_messages)

        if intent == "price":
            return await self.respond_price(tea_info, rewritten_data, results, history_messages)
        
        if intent == "caffeine":
            return await self.respond_caffeine(tea_info, rewritten_data, results, history_messages)
        
        if intent == "ingredients":
            return await self.respond_ingredients(tea_info, rewritten_data, results, history_messages)
        

        return await self.respond_other(tea_info, rewritten_data, results, history_messages)
        
    async def respond_price(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]
        intent = rewritten_data["intent"]
        target_scope = rewritten_data.get("target_scope") or "single"

        print("DEBUG: price-intent:", intent, "Question:", normalized_query, "Target Scope:",target_scope)
        
        documents = results["documents"][0]
        if documents:
            rag_context = "\n\n".join(documents)
        else:
            rag_context = ""

        if target_scope == "all_recommended":
            tea_ids = self.chat_history.get_last_recommendation()
            if not tea_ids:
                return "Ich kann mich leider nicht mehr an die Empfohlenen Tees erinnern."
            teas = [self.tea_repo.get_by_id(tid) for tid in tea_ids]
            
            recommended = []
            for tea in teas:
                recommended.append({
                    "tea_id": tea["id"],
                    "tea_name": tea.get("name"),
                    "category": tea.get("category"),
                    "price_eur": tea.get("price_eur"),
                    "has_caffeine": tea.get("has_caffeine"),
                    "ingredients": tea.get("ingredients"),
                })
            
            data_structure = {
                "intent": "price",
                "recommended_teas": recommended,
            }

        else:

            data_structure = {
                "intent": "price",
                "tea_name": tea_info.get("name"),
                "tea_id": tea_info.get("id"),
                "price_eur": tea_info.get("price_eur")
            }

        user_prompt = self.prompt_factory.price_respond_prompt(data_structure=data_structure, normalized_query=normalized_query, rag_context=rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.2,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()
    
    async def respond_recommendation(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]
        intent = rewritten_data["intent"]

        raw_aspects = rewritten_data.get("aspects") or []
        if isinstance(raw_aspects, str):
            aspects = {raw_aspects}
        else:
            aspects = set(raw_aspects)

        print("DEBUG: recommendation-intent:", intent, "Question:", normalized_query)

        documents = results["documents"][0]
        if not documents:
            return "Dazu habe ich in meinen Daten leider keine Informationen gefunden."
        
        rag_context = "\n\n".join(documents)

        tea_ids = results["ids"][0]

        teas_raw = [self.tea_repo.get_by_id(tid) for tid in tea_ids]
        final_teas = FilterController.filter_candidates(teas_raw, rewritten_data)

        final_ids = [t["id"] for t in final_teas]
        self.chat_history.remember_recommendation(tea_ids=final_ids)

        candidates = []
        for rank, tea in enumerate(final_teas, start=1):
            candidates.append({
                "rank": rank,
                "tea_id": tea["id"],
                "tea_name": tea.get("name"),
                "category": tea.get("category"),
                "price_eur": tea.get("price_eur"),
                "has_caffeine": tea.get("has_caffeine"),
                "ingredients": tea.get("ingredients"),
            })

        data_structure = {
            "intent": "recommendation",
            "aspects": list(aspects),
            "candidate_teas": candidates,
        }

        user_prompt = self.prompt_factory.recommendation_respond_prompt(data_structure, normalized_query, rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()
    
    async def respond_gift_recommendation(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]
        intent = rewritten_data["intent"]

        use_cases = rewritten_data.get("use_cases", [])
        recipient_type = rewritten_data.get("recipient_type")
        budget_min = rewritten_data.get("budget_min")
        budget_max = rewritten_data.get("budget_max")

        raw_aspects = rewritten_data.get("aspects", [])
        if isinstance(raw_aspects, str):
            aspects = {raw_aspects}
        else:
            aspects = set(raw_aspects)
        
        print("DEBUG: gift-recommendation-intent:", intent, "Question:", normalized_query, "use_cases:", use_cases, "recipient_type:", recipient_type)

        documents = results["documents"][0]
        if documents:
            rag_context = "\n\n".join(documents)
        else:
            rag_context = ""

        tea_ids = results["ids"][0]

        teas_raw = [self.tea_repo.get_by_id(tid) for tid in tea_ids]
        final_teas = FilterController.filter_candidates(teas_raw, rewritten_data)

        final_ids = [t["id"] for t in final_teas]
        self.chat_history.remember_recommendation(tea_ids=final_ids)

        candidates = []
        for rank, tea in enumerate(final_teas, start=1):
            candidates.append({
                "rank": rank,
                "tea_id": tea["id"],
                "tea_name": tea.get("name"),
                "category": tea.get("category"),
                "price_eur": tea.get("price_eur"),
                "has_caffeine": tea.get("has_caffeine"),
                "ingredients": tea.get("ingredients"),
            })

        data_structure = {
            "intent": "gift_recommendation",
            "aspects": list(aspects),
            "use_cases": use_cases,
            "recipient_type": recipient_type,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "candidate_teas": candidates,
        }

        user_prompt = self.prompt_factory.gift_recommendation_respond_prompt(data_structure, normalized_query, rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.2,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()
    
    async def respond_caffeine(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]
        intent = rewritten_data["intent"]
        target_scope = rewritten_data.get("target_scope") or "single"
        print("DEBUG: caffeine-intent:", intent, "Question:", normalized_query, "Target Scope", target_scope)

        documents = results["documents"][0]
        if documents:
            rag_context = "\n\n".join(documents)
        else:
            rag_context = ""

        if target_scope == "all_recommended":
            tea_ids = self.chat_history.get_last_recommendation()
            if not tea_ids:
                return "Ich kann mich leider nicht mehr an die Empfohlenen Tees erinnern."
            teas = [self.tea_repo.get_by_id(tid) for tid in tea_ids]

            recommended = []
            for tea in teas:
                recommended.append({
                    "tea_id": tea["id"],
                    "tea_name": tea.get("name"),
                    "category": tea.get("category"),
                    "price_eur": tea.get("price_eur"),
                    "has_caffeine": tea.get("has_caffeine"),
                    "ingredients": tea.get("ingredients"),
                })

            data_structure = {
                "intent": "caffeine",
                "recommended_teas": recommended,
            }
        
        else:
            data_structure = {
                "intent": "caffeine",
                "tea_name": tea_info.get("name"),
                "tea_id": tea_info.get("id"),
                "has_caffeine": tea_info.get("has_caffeine"),
            }

        user_prompt = self.prompt_factory.caffein_respond_prompt(data_structure, normalized_query, rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.2,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()
    
    async def respond_ingredients(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]
        intent = rewritten_data["intent"]
        target_scope = rewritten_data.get("target_scope") or "single"
        print("DEBUG: ingredients-intent:", intent, "Quiestion:", normalized_query)

        documents = results["documents"][0]
        if documents:
            rag_context = "\n\n".join(documents)
        else:
            rag_context = ""

        if target_scope == "all_recommended":
            tea_ids = self.chat_history.get_last_recommendation()
            if not tea_ids:
                return "Ich kann mich leider nicht mehr an die Empfohlenen Tees erinnern."
            teas = [self.tea_repo.get_by_id(tid) for tid in tea_ids]

            recommended = []
            for tea in teas:
                recommended.append({
                    "tea_id": tea["id"],
                    "tea_name": tea.get("name"),
                    "category": tea.get("category"),
                    "price_eur": tea.get("price_eur"),
                    "has_caffeine": tea.get("has_caffeine"),
                    "ingredients": tea.get("ingredients"),
                })

            data_structure = {
                "intent": "ingredients",
                "recommended_teas": recommended,
            }

        else:
            data_structure = {
                "intent": "ingredients",
                "tea_name": tea_info.get("name"),
                "tea_id": tea_info.get("id"),
                "ingredients": tea_info.get("ingredients"),
            }

        user_prompt = self.prompt_factory.ingredients_respond_prompt(data_structure, normalized_query, rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.2,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()

    async def respond_comparison(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]
        intent = rewritten_data["intent"]
        request_type = rewritten_data.get("request_type")

        raw_aspects = rewritten_data.get("aspects") or []
        if isinstance(raw_aspects, str):
            aspects = {raw_aspects}
        else:
            aspects = set(raw_aspects)

        print("DEBUG: comparison-intent:", intent, "Question:", normalized_query)

        documents = results["documents"][0]
        if documents:
            rag_context = "\n\n".join(documents)
        else:
            rag_context = ""

        last_recommended_ids = self.chat_history.get_last_recommendation()
        if last_recommended_ids:
            tea_ids = last_recommended_ids
            print("DEBUG: comparison using last_recommended_ids:", tea_ids)
        else:
            tea_ids = results["ids"][0]
            print("DEBUG: comparison using current RAG ids:", tea_ids)
        
        teas_raw = [self.tea_repo.get_by_id(tid) for tid in tea_ids]
        filtered = [t for t in teas_raw if t["base_type"] == request_type]
        if len(filtered) >= 3:
            final_teas = filtered[:3]
        else:
            remaining = 3 - len(filtered)
            filtered_ids = {t["id"] for t in filtered}
            extra = [t for t in teas_raw if t["id"] not in filtered_ids]
            final_teas = filtered + extra[:remaining]

        if len(final_teas) < 2:
            single = final_teas[0] if final_teas else None
            if single:
                return f"Ich habe nur einen passenden Tee gefunden: '{single['name']}'."
            else:
                return "Ich konnte keine passenden Tees zum Vergleichen finden."
            
        candidates = []
        for rank, tea in enumerate(final_teas, start=1):
            candidates.append({
                "rank": rank,
                "tea_id": tea["id"],
                "tea_name": tea.get("name"),
                "category": tea.get("category"),
                "price_eur": tea.get("price_eur"),
                "has_caffeine": tea.get("has_caffeine"),
                "ingredients": tea.get("ingredients"),
            })
        
        data_structure = {
            "intent": "comparison",
            "aspects": list(aspects),
            "candidate_teas": candidates,
        }

        user_prompt = self.prompt_factory.comparison_respond_prompt(data_structure, normalized_query, rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.2,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()

    async def respond_multi(self, tea_info, rewritten_data, results, history_messages):
        if tea_info is None:
            return "Ich konnte den passenden Tee leider nicht eindeutig bestimmen."
        
        normalized_query = rewritten_data["normalized_query"]

        raw_aspects = rewritten_data.get("aspects") or []
        if isinstance(raw_aspects, str):
            aspects = {raw_aspects}
        else:
            aspects = set(raw_aspects)
        print("DEBUG: multi-intent aspects:", aspects, "Question:", normalized_query)

        documents = results["documents"][0]

        if documents:
            rag_context = "\n\n".join(documents)
        else:
            rag_context = ""

        data_structure = {
            "intent": "multi",
            "aspects": list(aspects),
            "tea_name": tea_info.get("name"),
            "tea_id": tea_info.get("id"),
        }
        for aspect in aspects:
            mapping = ASPECT_FIELD_MAP.get(aspect)
            if not mapping:
                continue
            target_key, source_key = mapping
            data_structure[target_key] = tea_info.get(source_key)

        user_prompt = self.prompt_factory.multi_respond_prompt(data_structure, normalized_query, rag_context)

        api_message = history_messages + [
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=api_message,
            n=1,
        )

        return response.choices[0].message.content.strip()

    async def respond_cross_sell(self, tea_info, rewritten_data, results, history_messages):
        normalized_query = rewritten_data["normalized_query"]
        cross_sell_target = rewritten_data.get("cross_sell_target")
        budget_min = rewritten_data.get("budget_min")
        budget_max = rewritten_data.get("budget_max")

        print("DEBUG: cross_sell_intent:", normalized_query,
              "target:", cross_sell_target,
              "budget:", budget_min, budget_max)
        
        documents = results["documents"][0]

        if documents:
            rag_context = "\n\n".join(documents)        # Optional for later
        else:
            rag_context = ""
        
        ids_lists = results.get("ids", [])
        if not ids_lists or not ids_lists[0]:
            return(
                "Ich konnte gerade kein passendes Zubehör finden." \
                "Frage mich bitte konkreter nach z.B. Glas, Kanne, Filter oder Geschenksets"
            )
        
        accessory_ids = ids_lists[0]

        accessory_candidates = []
        for acc_id in accessory_ids:
            product = self.tea_repo.get_product_by_id(acc_id)
            if not product:
                continue
            if product.get("type") != "accessory":
                continue

            price = product.get("price_eur")
            if budget_min is not None and price is not None and price < budget_min:
                continue
            if budget_max is not None and price is not None and price > budget_max:
                continue

            accessory_candidates.append({
                "id": product["id"],
                "name": product["name"],
                "price_eur": price,
                "category": product.get("category"),
                "image_url": product.get("image_url"),
                "attributes": product.get("attributes", {})
            })

        if not accessory_candidates:
            return (
                "Ich konnte in deinem Budgetbereich gerade kein passendes Zubehör finden."
                "Wenn du möchtest, kann ich dir trotzdem generelles Zubehör empfehlen."
            )
        
        accessory_candidates = accessory_candidates[:5]

        tea_context = []
        if cross_sell_target == "last_recommended":
            for tea_id in self.chat_history.last_recommended_ids:
                t = self.tea_repo.get_by_id(tea_id)
                if not t:
                    continue

                tea_context.append({
                    "id": t["id"],
                    "name": t["name"],
                    "category": t.get("category"),
                    "base_type": t.get("base_type"),
                    "has_caffeine": t.get("has_caffeine"),
                })

        data_structure = {
            "intent": "cross_sell",
            "cross_sell_target": cross_sell_target,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "base_teas": tea_context,
            "candidate_products": accessory_candidates,
        }

        user_prompt = self.prompt_factory.cross_sell_respond_prompt(
            data_structure=data_structure,
            normalized_query=normalized_query,
            rag_context=rag_context,
        )

        api_message = history_messages + [
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.2,
            messages=api_message,
            n=1,
        )
        
        return response.choices[0].message.content.strip()

    
    async def respond_other(self, tea_info, rewritten_data, results, history_messages):
        rewritten_query = rewritten_data["normalized_query"]

        prompt_creator = PromptCreation(user_query=rewritten_query, collection=None, results=results)
        user_prompt = prompt_creator.generate_prompt()
        api_message = history_messages + [
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=api_message,
            n=1
        )

        return response.choices[0].message.content.strip()
    