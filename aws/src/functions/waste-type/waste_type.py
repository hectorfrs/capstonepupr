import datetime
import json
import time
import boto3


def get_event_date(event):
    """Obtiene la fecha del evento a partir del timestamp."""
    if "timestamp" in event[0]:
        mytimestamp = datetime.datetime.fromtimestamp(event[0]["timestamp"])
    else:
        mytimestamp = datetime.datetime.fromtimestamp(time.time())
    return mytimestamp.strftime("%Y%m%d")


def classify_waste(labels):
    """
    Clasifica los tipos de plásticos y residuos según etiquetas detectadas.
    """
    # Clasificación por tipo de plástico
    plastic_types = {
        "PET": ["bottle", "polyethylene"],
        "HDPE": ["container", "high-density polyethylene"],
        "PVC": ["pipe", "polyvinyl chloride"],
        "LDPE": ["bag", "low-density polyethylene"],
        "PP": ["cap", "polypropylene"],
        "PS": ["foam", "polystyrene"],
        "Other": ["plastic"],
    }

    # Otras categorías de residuos
    organic_waste_dict = [
        "orange", "bread", "banana", "orange peel", "apple", "onion",
        "vegetable", "potato"
    ]
    solid_waste_dict = [
        "cardboard", "paper", "bottle", "polythene", "paper ball"
    ]
    hazardous_waste_dict = ["batteries"]

    # Inicialización de contadores
    classification = {ptype: 0 for ptype in plastic_types.keys()}
    organic_waste = 0
    solid_waste = 0
    hazardous_waste = 0
    other_waste = 0
    detected_items = []

    for label in labels:
        found = False

        # Clasificación por tipo de plástico
        for ptype, keywords in plastic_types.items():
            if label["Name"].lower() in keywords:
                classification[ptype] += 1
                detected_items.append({"Name": label["Name"], "Confidence": label["Confidence"]})
                found = True
                break

        # Clasificación adicional si no es plástico
        if not found:
            if label["Name"].lower() in organic_waste_dict:
                organic_waste += 1
                detected_items.append({"Name": label["Name"], "Confidence": label["Confidence"]})
            elif label["Name"].lower() in solid_waste_dict:
                solid_waste += 1
                detected_items.append({"Name": label["Name"], "Confidence": label["Confidence"]})
            elif label["Name"].lower() in hazardous_waste_dict:
                hazardous_waste += 1
                detected_items.append({"Name": label["Name"], "Confidence": label["Confidence"]})
            else:
                other_waste += 1
                detected_items.append({"Name": label["Name"], "Confidence": label["Confidence"]})

    return classification, organic_waste, solid_waste, hazardous_waste, other_waste, detected_items


def lambda_handler(event, context):
    """
    Función principal que procesa un evento y clasifica residuos y plásticos.
    """
    if len(event) > 0 and "s3_image_uri" in event[0]:
        print(f"Received Event: {event}")
        bucket_url = event[0]["s3_image_uri"]
        output = bucket_url.split("/", 3)
        bucket = output[2]
        photo = output[3]
        client = boto3.client("rekognition")

        try:
            time.sleep(5)
            # Realizar detección de etiquetas en la imagen
            response = client.detect_labels(
                Image={"S3Object": {"Bucket": bucket, "Name": photo}}, MaxLabels=10
            )
            labels = response["Labels"]
            classification, organic_waste, solid_waste, hazardous_waste, other_waste, detected_items = classify_waste(
                labels
            )

            # Añadir información al evento
            event[0]["waste_data"] = {
                "classification": classification,
                "organic_waste": organic_waste,
                "solid_waste": solid_waste,
                "hazardous_waste": hazardous_waste,
                "other_waste": other_waste,
                "detected_items": detected_items,
                "event_date": get_event_date(event),
            }
        except Exception as ex:
            print(f"Error en Rekognition: {ex}")
            # Manejo de errores: Retorna datos vacíos
            event[0]["waste_data"] = {
                "classification": {ptype: 0 for ptype in ["PET", "HDPE", "PVC", "LDPE", "PP", "PS", "Other"]},
                "organic_waste": 0,
                "solid_waste": 0,
                "hazardous_waste": 0,
                "other_waste": 0,
                "detected_items": [],
                "event_date": get_event_date(event),
            }
    else:
        # Si no hay datos válidos en el evento
        event[0]["waste_data"] = {
            "classification": {ptype: 0 for ptype in ["PET", "HDPE", "PVC", "LDPE", "PP", "PS", "Other"]},
            "organic_waste": 0,
            "solid_waste": 0,
            "hazardous_waste": 0,
            "other_waste": 0,
            "detected_items": [],
            "event_date": get_event_date(event),
        }

    print(f"Processed Event: {event}")
    return event
