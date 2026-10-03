import json
from app.core.config import JSON_PATH

class TeaRepository:        # Jetzt allgemeines Repository lol
    def __init__(self, json_path=JSON_PATH):
        self.products = {}

        self.teas = {}
        self.accessories = {}

        self.ids = []
        self.rag_text = []
        self.metadatas = []

        self.load_data(json_path)
    
    def load_data(self, json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: File {json_path} not Found!")
            products = []

        for p in products:
            if not p.get("active", True):
                continue

            attrs = p.get("attributes", {})

            p_type = p.get("type")
            category = p.get("category")
            base_type = category

            product_data = {
                "id": p["id"],
                "type": p_type,
                "name": p["name"],
                "price_eur": p["price_eur"],
                "category": category,
                "base_type": base_type,
                "use_cases": p.get("use_cases", []),
                "occasion_tags": p.get("occasion_tags", []),
                "recipient_tags": p.get("recipient_tags", []),
                "cross_sell_tags": p.get("cross_sell_tags", []),
                "image_url": p.get("image_url"),
            }

            if p_type == "tea":
                product_data["has_caffeine"] = bool(attrs.get("caffeine", False))
                product_data["ingredients"] = (attrs.get("ingredients", []) if "ingredients" in attrs else "Keine Angabe")
                product_data["brewing_time_min"] = (attrs.get("brewing_time_min", "Keine Angabe"))
                product_data["brewing_time_max"] = (attrs.get("brewing_time_max", "Keine Angabe"))
                product_data["temperature"] = (attrs.get("temperature", "Keine Angabe"))
            
            else:
                product_data["attributes"] = attrs

            self.products[p["id"]] = product_data

            if p_type == "tea":
                self.teas[p["id"]] = product_data
            elif p_type == "accessory":
                self.accessories[p["id"]] = product_data
            else:
                pass

            rag_text = self.generate_rag_text(p, product_data)
            product_data["rag_text"] = rag_text

            self.ids.append(p["id"])
            self.rag_text.append(rag_text)

            metadata = {
                "id": p["id"],
                "type": p_type,
                "name": p["name"],
                "price_eur": p["price_eur"],
                "category": category,
                "base_type": category,
            }

            if p_type == "tea":
                metadata["has_caffeine"] = bool(attrs.get("caffeine", False))
                metadata["ingredients"] = ", ".join(attrs.get("ingredients", []))
            
            self.metadatas.append(metadata)

    def generate_rag_text(self, p, product_data):
        attrs = p.get("attributes", {})
        p_type = product_data.get("type", "tea")

        name = p.get("name", "")
        category = p.get("category", "")
        description = p.get("description", "")
        price = p.get("price_eur")

        if p_type == "tea":
            caff_str = "Ja" if attrs.get("caffeine") else "Nein"
            ingredients = product_data.get("ingredients", "Keine Angabe")
            taste_profile = ", ".join(attrs.get("taste_profile", []))
            brewing_time_min = product_data.get("brewing_time_min", "Keine Angabe")
            brewing_time_max = product_data.get("brewing_time_max", "Keine Angabe")
            temperature = product_data.get("temperature", "Keine Angabe")

            text = f"""
            Name: {name}
            Kategorie: {category}
            Beschreibung: {description}
            Inhaltsstoffe: {ingredients}
            Geschmack: {taste_profile}
            Zubereitung: {brewing_time_min}min bis {brewing_time_max}min bei {temperature} °C
            Preis: {price}€
            Koffein: {caff_str}
            """
        
        else:
            extra_lines = []

            for key, value in attrs.items():
                if value is None:
                    continue
                extra_lines.append(f"{key}: {value}")
            
            extra_str = "\n".join(extra_lines)

            text = f"""
            Produkttyp: {p_type}
            Name: {name}
            Kategorie: {category}
            Beschreibung: {description}
            Preis: {price}€
            {extra_str}
            """
        
        return text.strip()

    def get_by_id(self, tea_id):        # only for teas -> has to get yeeted
        teas = self.teas

        return teas.get(tea_id)
    
    def get_price(self, tea_id):        # only for teas -> has to get yeeted
        teas = self.teas

        return teas[tea_id]["price_eur"]
    
    def has_caffeine(self, tea_id):     # only for teas -> has to get yeeted
        teas = self.teas

        return teas[tea_id]["has_caffeine"]
    
    def get_data_for_db(self):
        return self.rag_text, self.ids, self.metadatas
    
    # overall data (change the above to these except get_data_for_db)
    def get_product_by_id(self, product_id):
        return self.products.get(product_id)
    
    def get_accessory_by_id(self, accessory_id):
        return self.accessories.get(accessory_id)
    
    def get_all_teas(self):
        return list(self.teas.values())
    
    def get_all_accessories(self):
        return list(self.accessories.values())