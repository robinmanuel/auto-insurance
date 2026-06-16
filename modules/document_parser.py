import re


class DocumentParser:

    def parse(self, document_type, text):

        if document_type == "DRIVING_LICENSE":
            return self.parse_dl(text)

        if document_type == "RC_BOOK":
            return self.parse_rc(text)

        if document_type == "INVOICE":
            return self.parse_invoice(text)

        return {}

    # -------------------------
    # Driving License
    # -------------------------

    def parse_dl(self, text):

        data = {}

        dl = re.search(
            r"[A-Z]{2}\d{2}\s?\d{8,15}",
            text
        )

        data["license_number"] = (
            dl.group(0)
            if dl else None
        )

        data["dates"] = re.findall(
            r"\d{2}[-/.]\d{2}[-/.]\d{4}",
            text
        )

        names = []

        for word in text.split():

            word = word.strip()

            if (
                word.isupper()
                and len(word) > 3
                and not any(c.isdigit() for c in word)
            ):
                names.append(word)

        data["name"] = names[0] if names else None

        return data

    # -------------------------
    # RC BOOK
    # -------------------------

    def parse_rc(self, text):

        data = {}

        clean = text.upper().replace(" ", "")

        vehicle = re.search(
            r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}",
            clean
        )

        data["vehicle_number"] = (
            vehicle.group(0)
            if vehicle else None
        )

        chassis = re.findall(
            r"[A-Z0-9]{15,25}",
            clean
        )

        data["chassis_number"] = (
            max(chassis, key=len)
            if chassis else None
        )

        engine = re.findall(
            r"[A-Z0-9]{10,20}",
            clean
        )

        data["engine_number"] = (
            engine[0]
            if engine else None
        )

        return data

    # -------------------------
    # Invoice
    # -------------------------

    def parse_invoice(self, text):

        data = {}

        amounts = re.findall(
            r"\d+(?:,\d+)*(?:\.\d+)?",
            text
        )

        values = []

        for a in amounts:
            try:
                values.append(
                    float(a.replace(",", ""))
                )
            except:
                pass

        data["invoice_amount"] = (
            max(values)
            if values else 0
        )

        dates = re.findall(
            r"\d{2}[-/][A-Za-z]{3}[-/]\d{2,4}",
            text
        )

        data["invoice_dates"] = dates

        return data