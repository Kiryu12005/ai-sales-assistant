
class FilterController:
    @staticmethod
    def filter_candidates(candidates: list, criteria: dict) -> list:
        filtered = candidates

        request_type = criteria.get("request_type")
        request_ingredients = criteria.get("request_ingredients", [])

        # base_type filter:
        if request_type:
            filtered = [t for t in filtered if t.get("base_type") == request_type]
        
        # ingredients filter:
        if request_ingredients:
            for req_ing in request_ingredients:
                filtered = [
                    tea for tea in filtered
                    if req_ing.lower() in ", ".join(tea.get("ingredients", [])).lower()
                ]

        return filtered
    
    @staticmethod
    def filter_gift_candidates(candidates: list, criteria: dict) -> list:
        base_filtered = FilterController.filter_candidates(candidates, criteria)

        use_cases = criteria.get("use_cases", [])
        use_cases = [u.lower() for u in use_cases if isinstance(u, str)]

        recipient_type = criteria.get("recipient_type")
        if isinstance(recipient_type, str):
            recipient_type = recipient_type.lower()
        else:
            recipient_type = None

        budget_min = criteria.get("budget_min")
        budget_max = criteria.get("budget_max")

        def in_budget(p):
            price = p.get("price_eur")

            if price is None:
                return False
            elif budget_min is not None and price < budget_min:
                return False
            elif budget_max is not None and price > budget_max:
                return False
            else:
                return True
    
        if budget_min is not None or budget_max is not None:
            budget_filtered = [p for p in base_filtered if p and in_budget(p)]
            filtered = budget_filtered or base_filtered
        else:
            filtered = base_filtered

        def gift_score(p):
            score = 0

            p_use_cases = set(p.get("use_cases", []))
            p_occasion = set(p.get("occasion_tags", []))        # for later with occasion tags
            p_recipient = set(p.get("recipient_tags", []))

            if "gift" in use_cases and "gift" in {x.lower() for x in p_use_cases}:
                score += 3

            if recipient_type and recipient_type in {x.lower() for x in p_recipient}:
                score += 4
            
            return score
        
        filtered_with_scores = [(p, gift_score(p)) for p in filtered]
        filtered_with_scores.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in filtered_with_scores]