class PromptCreation:
    def __init__(self, user_query, collection, results):
        self.user_query = user_query
        self.collection = collection
        self.results = results
    
    def generate_prompt(self):
        user_query = self.user_query

        retrieve_documents = self.results["documents"][0]
        if not retrieve_documents:
            return "Dazu habe ich in meinen Daten leider keine Informationen gefunden."
        
        context = "\n\n".join(retrieve_documents)
        
        self.user_prompt = f"""
        KONTEXT: {context}

        KUNDENFRAGE: {user_query}
        """

        return self.user_prompt