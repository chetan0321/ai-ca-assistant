# gst_engine.py

def generate_gstr1(transactions, user_state="07"):  # Default to e.g. Delhi (07)
    b2b = []
    b2c_large = []
    exports = []
    b2c_small = {}  # key: (state, tax_rate), value: total taxable value, tax amounts

    for t in transactions:
        place = str(t.get("place_of_supply", "")).strip()
        party_gstin = str(t.get("party_gstin", "")).strip()
        taxable = float(t.get("taxable_value", 0))
        tax_rate = float(t.get("tax_rate", 0))
        cgst = float(t.get("cgst", 0))
        sgst = float(t.get("sgst", 0))
        igst = float(t.get("igst", 0))

        # Determine category
        if place.lower() in ["outside india", "sez"]:
            exports.append(t)
        elif party_gstin and party_gstin.lower() not in ["none", "nan", ""]:  # B2B
            b2b.append(t)
        else:  # B2C
            is_inter_state = (place != user_state)
            if is_inter_state and taxable > 250000:
                b2c_large.append(t)
            else:
                key = (place, tax_rate)
                if key not in b2c_small:
                    b2c_small[key] = {"taxable": 0, "cgst": 0, "sgst": 0, "igst": 0}
                b2c_small[key]["taxable"] += taxable
                b2c_small[key]["cgst"] += cgst
                b2c_small[key]["sgst"] += sgst
                b2c_small[key]["igst"] += igst

    # Build final GSTR-1 JSON
    gstr1 = {
        "gstin": "USER_GSTIN",  # placeholder, we'll get from user later
        "fp": "032026",  # e.g. Mar 2026
        "b2b": [
            {
                "ctin": t["party_gstin"],
                "inv": [{
                    "inum": t["invoice_number"],
                    "idt": t["date"],
                    "val": float(t.get("taxable_value", 0)) + float(t.get("igst", 0)) + float(t.get("cgst", 0)) + float(t.get("sgst", 0)),
                    "itms": [{
                        "num": 1,
                        "itm_det": {
                            "txval": float(t.get("taxable_value", 0)),
                            "rt": float(t.get("tax_rate", 0)),
                            "iamt": float(t.get("igst", 0)),
                            "camt": float(t.get("cgst", 0)),
                            "samt": float(t.get("sgst", 0))
                        }
                    }]
                }]
            } for t in b2b
        ],
        "b2cl": [
            {
                "pos": str(t.get("place_of_supply", "")),
                "inv": [{
                    "inum": t["invoice_number"],
                    "idt": t["date"],
                    "val": float(t.get("taxable_value", 0)) + float(t.get("igst", 0)) + float(t.get("cgst", 0)) + float(t.get("sgst", 0)),
                    "itms": [{
                        "num": 1,
                        "itm_det": {
                            "txval": float(t.get("taxable_value", 0)),
                            "rt": float(t.get("tax_rate", 0)),
                            "iamt": float(t.get("igst", 0)),
                            "camt": float(t.get("cgst", 0)),
                            "samt": float(t.get("sgst", 0))
                        }
                    }]
                }]
            } for t in b2c_large
        ],
        "exp": [
            {
                "exp_typ": "WPAY" if str(t.get("place_of_supply", "")).lower() == "outside india" else "SEZWP",
                "inv": [{
                    "inum": t["invoice_number"],
                    "idt": t["date"],
                    "val": float(t.get("taxable_value", 0)),
                    "itms": [{
                        "num": 1,
                        "itm_det": {
                            "txval": float(t.get("taxable_value", 0)),
                            "rt": float(t.get("tax_rate", 0)),
                            "iamt": float(t.get("igst", 0)),
                            "camt": 0,
                            "samt": 0
                        }
                    }]
                }]
            } for t in exports
        ],
        "b2cs": [
            {
                "pos": state,
                "rt": tax_rate,
                "txval": round(data["taxable"], 2),
                "iamt": round(data["igst"], 2),
                "camt": round(data["cgst"], 2),
                "samt": round(data["sgst"], 2)
            } for (state, tax_rate), data in b2c_small.items()
        ]
    }
    return gstr1

def generate_gstr3b(transactions):
    total_taxable = sum(float(t.get("taxable_value", 0)) for t in transactions)
    total_cgst = sum(float(t.get("cgst", 0)) for t in transactions)
    total_sgst = sum(float(t.get("sgst", 0)) for t in transactions)
    total_igst = sum(float(t.get("igst", 0)) for t in transactions)
    
    gstr3b = {
        "gstin": "USER_GSTIN",
        "fp": "032026",
        "sup_details": {
            "osup_det": {
                "txval": round(total_taxable, 2),
                "iamt": round(total_igst, 2),
                "camt": round(total_cgst, 2),
                "samt": round(total_sgst, 2)
            }
        },
        "itc_elg": {
            "itc_avl": {
                "iamt": 0,   # Computable from purchase invoices (later phase)
                "camt": 0,
                "samt": 0
            }
        }
    }
    return gstr3b

def detect_errors(transactions):
    errors = []
    for i, t in enumerate(transactions):
        txn_idx = i + 1
        
        # Check missing invoice
        if str(t.get("invoice_number", "")).strip() in ["", "nan", "None"]:
            errors.append({
                "transaction_index": txn_idx,
                "error": "Missing Invoice Number",
                "severity": "high"
            })
            
        rate_raw = t.get("tax_rate", 0)
        try:
            rate = float(rate_raw)
        except (ValueError, TypeError):
            rate = -1
            
        if rate not in [0.0, 5.0, 12.0, 18.0, 28.0]:
            errors.append({
                "transaction_index": txn_idx,
                "error": f"Invalid or missing tax rate: '{rate_raw}'. Valid rates are 0, 5, 12, 18, 28.",
                "severity": "high"
            })
            
        if t.get("taxable_value", 0) == 0:
            errors.append({
                "transaction_index": txn_idx,
                "error": "Taxable value is 0 or missing.",
                "severity": "medium"
            })
            
    return errors
