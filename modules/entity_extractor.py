import re
import spacy


class EntityExtractor:

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text):

        doc = self.nlp(text)

        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "license_numbers": [],
            "vehicle_numbers": [],
            "policy_numbers": [],
            "engine_numbers": [],
            "chassis_numbers": []
        }

        for ent in doc.ents:

            if ent.label_ == "PERSON":
                entities["persons"].append(ent.text)

            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)

            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(ent.text)

            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)

        clean = re.sub(r"[^A-Z0-9\s/-]", " ", text.upper())

        entities["license_numbers"] = list(set(
            re.findall(r"[A-Z]{2}\d{2}\s?\d{7,15}", clean)
        ))

        entities["vehicle_numbers"] = list(set(
            re.findall(r"[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,4}", clean)
        ))

        entities["engine_numbers"] = list(set(
            re.findall(r"[A-Z0-9]{10,25}", clean)
        ))

        entities["chassis_numbers"] = list(set(
            re.findall(r"[A-Z0-9]{17}", clean)
        ))

        return entities