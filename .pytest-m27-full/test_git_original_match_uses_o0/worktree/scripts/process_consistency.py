def evaluate(case):
    kind = case["kind"]
    difference = case["difference"]
    if kind == "qa_shipment_quantity":
        anomalous = difference > 0
    elif kind == "other":
        anomalous = difference > 0
    return anomalous
