import json

class PromptFactory:
    @staticmethod
    def price_respond_prompt(data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem Deutsch für einen Kunden des Tee Geschäftes.
        - Falls in STRUKTURIERTE_DATEN Felder für genau EINEN Tee vorhanden sind:
            - Nenne umbedingt den Preis in Euro.
            - Du DARFST Formulierungen variiren, aber du DARFST den Preis oder den Tee-Namen NICHT verändern.
            - Erfinde KEINE zusätzlichen Preise oder Produkte.
            - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        - Falls "recommended_teas" vorhanden ist:
            - Nenne umbedingt für ALLE Tees in "recommended_teas" den Namen und den Preis in Euro.
            - Du DARFST Formulierungen variiren, aber du DARFST Preise oder Tee-Namen NICHT verändern.
            - Erfinde KEINE zusätzlichen Preise oder Produkte.
            - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        """

        return user_prompt
    
    def recommendation_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem Deutsch für einen Kunden (für den du der Berater bist) des Tee Geschäftes.
        - Nenne umbedingt 2-3 der oben aufgeführten Tees, die am besten zur Kundenfrage passen.
        - Für jeden ausgewählten Tee: nenne den Namen und eine kurze Beschreibung des Tees.
        - Falls Aspekte in "aspects" vorhanden sind:
            - Wenn "price" in "aspects" enthalten ist, nenne für jeden empfohlenen Tee den Preis in Euro.
            - Wenn "caffeine" in "aspects" enthalten ist, sage klar, ob die empfohlenen Tees koffeinhaltig oder koffeinfrei sind.
            - Wenn "ingredients" in "aspects" enthalten ist, gehe kurz auf die wichtigsten Inhaltsstoffe ein.
        - Verwende AUSSCHLIESSLICH die Tees aus "candidate_teas" und erfinde KEINE neuen Produkte
        - Du DARFST Formulierungen variiren, aber du DARFST die Informationen von dem Tee oder den Tee namen NICHT verändern.
        - Erfinde KEINE zusätzlichen informationen zu Produkten.
        - Falls die Frage sehr allgemein ist, erkläre kurz, warum diese Tees gut passen.
        - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        """

        return user_prompt
    
    def caffein_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE: 
        Formuliere eine kurze, freundliche Antwort in natürlichem Deutsch für einen Kunden des Tee Geschäftes.
        - Falls in STRUKTURIERTE_DATEN Felder für genau EINEN Tee vorhanden sind:
            - Nenne umbedingt ob der ob der ausgewählte Tee Koffein enthalten hat oder nicht.
            - Du DARFST Formulierungen variiren, aber du DARFST den Tee-Namen oder, ob der Tee Koffein enthalten hat oder nicht NICHT verändern.
            - Erfinde NICHT ob der Tee Koffein enthalten hat oder nicht.
            - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        - Falls "recommended_teas" vorhanden ist:
            - Nenne umbedingt für ALLE Tees in "recommended_teas" ob diese Tees Koffein enthalten haben oder nicht.
            - Du DARFST Formulierungen variiren, aber du DARFST die Tee-Namen oder, ob die Tees Koffein enthalten haben oder nicht NICHT verändern.
            - Erfinde NICHT ob die Tees Koffein enthalten haben oder nicht.
            - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        """

        return user_prompt
    
    def ingredients_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem Deutsch für einen Kunden des Tee Geschäftes.
        - Falls in STRUKTURIERTE_DATEN Felder für genau EINEN Tee vorhanden sind:
            - Nenne umbedingt die Inhaltsstoffe des ausgewählten Tees.
            - Du DARFST Formulierungen variiren, aber du DARFST den Tee-Namen oder die Inhaltsstoffe NICHT verändern.
            - Erfinde KEINE zusätzlichen Inhaltsstoffe oder Produkte.
            - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        - Falls "recommended_teas" vorhanden ist:
            - Nenne umbedingt die Inhaltsstoffe ALLER Tees in "recommended_teas".
            - Du DARFST Formulierungen variiren, aber du DARFST die Tee-Namen oder die Inhaltsstoffe der Tees NICHT verändern.
            - Erfinde KEINE zusätzlichen Inhaltsstoffe oder Produkte.
            - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        """

        return user_prompt
    
    def comparison_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem Deutsch für einen Kunden (für den du der Berater bist) des Tee Geschäftes.
        - Vergleiche die Tees in "candidate_teas" miteinander.
        - Gehe insbesondere auf folgende Punkte ein:
            - Geschmacksprofil
            - Koffein (koffeinfrei vs koffeinhaltig)
            - grobe Preisunterschiede
            - besondere Inhaltsstoffe (z.B. Ingwer, Minze, Zitrone, usw.)
        - Falls Aspekte in "aspects" vorhanden sind:
            - Wenn "price" in "aspects" enthalten ist, vergleiche die Preise der Tees genauer.
            - Wenn "caffeine" in "aspects" enthalten ist, vergleiche den koffeingehalt der Tees genauer.
            - Wenn "ingredients" in "aspects" enthalten ist, vergleiche die Inhaltsstoffe der Tees genauer.
        - Du DARFST Formulierungen variiren, aber formuliere klar die Unterschiede und für welchen Kundentypen welcher Tee am besten geeignet ist.
        - Verwende AUSSCHLIESSLICH die Tees aus "candidate_teas". Erfinde KEINE neuen Produkte, Preise oder Informationen.
        - Wenn aus der Frage spezielle Wünsche hervorgehen, beziehe sie in deine Empfehlung mit ein.
        - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        """

        return user_prompt
    
    def multi_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem Deutsch für einen Kunden des Tee Geschäftes.
        - Beantworte ALLE Aspekte in "aspects" in einer zusammenhängenden Antwort.
        - Du DARFST Formulierungen variiren, aber du DARFST Tee-Namen, Preise, Inhaltsstoffe oder Koffein-Status NICHT verändern.
        - Erfinde KEINE zusätzlichen Produkte oder Fakten.
        - Analysiere den Gesprächsfluss und formuliere die Antwort passend dazu.
        """
        
        return user_prompt
    
    def cross_sell_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem, gut lesbarem Deutsch 
        für einen Kunden des Tee-Geschäftes.

        WICHTIG:
        - Die STRUKTURIERTE_DATEN enthalten:
            - "base_teas": optional eine Liste von Tees, zu denen Zubehör gesucht wird.
            - "candidate_products": eine Liste von möglichen Zubehör-Artikeln.
            - "budget_min" / "budget_max": optionaler Budget-Rahmen in Euro.
        - Du DARFST NUR Zubehör aus "candidate_products" empfehlen, KEINE anderen Produkte.
        - Verändere KEINE Produktnamen, Preise oder Kategorien.
        - Erfinde KEINE zusätzlichen Produkte oder Fakten.

        VERHALTEN:
        - Wähle in der Regel 2-3 Zubehör-Produkte aus "candidate_products", die am besten zur FRAGE 
          und ggf. zu den "base_teas" passen.
        - Nutze das Budget, falls vorhanden:
            - Bevorzuge Produkte, deren Preis innerhalb von "budget_min" und "budget_max" liegt.
            - Wenn fast keine Produkte ins Budget passen, erkläre das kurz und empfehle die am besten passenden,
              auch wenn sie leicht außerhalb des Budgets liegen.
        - Begründe kurz, WARUM jedes empfohlene Zubehör sinnvoll ist 
          (z.B. passend zu Früchtetees, gut für Eistee, praktisch fürs Büro, schönes Geschenk usw.).
        - Nenne in der Antwort die Produktnamen klar, damit der Kunde sie im Shop wiederfindet.
        - Analysiere den bisherigen Gesprächsverlauf und formuliere die Antwort passend dazu.
        """

        return user_prompt
    
    def gift_recommendation_respond_prompt(self, data_structure, normalized_query, rag_context):
        user_prompt = f"""
        STRUKTURIERTE_DATEN (Wahrheitsquelle, NICHT verändern):
        {json.dumps(data_structure, ensure_ascii=False)}

        FRAGE: {normalized_query}

        KONTEXT (Zusatzinformationen zum Tee, optional):
        {rag_context}

        AUFGABE:
        Formuliere eine kurze, freundliche Antwort in natürlichem, gut lesbarem Deutsch
        für einen Kunden des Tee-Geschäftes.

        WICHTIG:
        - Die STRUKTURIERTE_DATEN enthalten:
            - "candidate_teas": mögliche Tees, die als Geschenk in Frage kommen.
            - "use_cases": z.B. "gift".
            - "recipient_type": z.B. "mother", "father", "friend", "colleague".
            - "budget_min" / "budget_max": optionaler Budget-Rahmen in Euro.
        - Du DARFST NUR Tees aus "candidate_teas" empfehlen, KEINE anderen Produkte.
        - Verändere KEINE Produktnamen, Preise oder Kategorien.
        - Erfinde KEINE zusätzlichen Produkte oder Fakten.

        VERHALTEN:
        - Gehe davon aus, dass der Nutzer ein GESCHENK sucht.
        - Beziehe "recipient_type" in die Empfehlung ein:
            - z.B. etwas Besonderes für "mother", eher neutral für "colleague", etc.
        - Berücksichtige das Budget, falls vorhanden:
            - Bevorzuge Tees, deren Preis im Budget liegt.
            - Wenn fast keine Tees ins Budget passen, erkläre das kurz und empfehle die am besten passenden.
        - Stelle 2-3 Geschenk-Tee-Empfehlungen vor.
        - Begründe kurz, warum diese Tees ein gutes Geschenk für diese Person sind.
        - Nenne die Produktnamen klar, damit der Kunde sie im Shop wiederfindet.
        - Analysiere den bisherigen Gesprächsverlauf und formuliere die Antwort passend dazu.
        """

        return user_prompt