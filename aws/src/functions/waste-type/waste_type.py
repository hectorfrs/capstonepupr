import datetime
import json
import time

import boto3


def get_event_date(event):
    if "timestamp" in event[0]:
        mytimestamp = datetime.datetime.fromtimestamp(event[0]["timestamp"])
    else:
        mytimestamp = datetime.datetime.fromtimestamp(time.time())
    return mytimestamp.strftime("%Y%m%d")


def lambda_handler(event, context):
    if len(event) > 0 and "s3_image_uri" in event[0]:
        print(event)
        bucket_url = event[0]["s3_image_uri"]
        output = bucket_url.split("/", 3)
        bucket = output[2]
        photo = output[3]
        client = boto3.client("rekognition")
        # process using S3 object
        try:
            time.sleep(5)
            # If using custom models, then please use below syntax
            # response = client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
            # MinConfidence=30,ProjectVersionArn=model_arn)
            response = client.detect_labels(
                Image={"S3Object": {"Bucket": bucket, "Name": photo}}, MaxLabels=10
            )
        except Exception as ex:
            print(ex)
            event[0]["sorted_waste"] = []
            event[0]["organic_waste"] = 0
            event[0]["solid_waste"] = 0
            event[0]["hazardous_waste"] = 0
            event[0]["plastic_types"] = {}
            event[0]["other_waste"] = 0
            return event
        # Get the custom labels
        # labels=response['CustomLabels']
        labels = response["Labels"]
        solid_waste = 0
        organic_waste = 0
        hazardous_waste = 0
        other_waste = 0
        sorted_waste_items = []
        # Dictionaries for waste categories
        organic_waste_dict = [
            "orange", "bread", "banana", "orange peel", "apple", "onion", 
            "vegetable", "potato"
        ]
        solid_waste_dict = [
            "cardboard", "plastic", "paper", "bottle", "polythene", "paper ball"
        ]
        hazardous_waste_dict = ["batteries"]
         # Plastic subcategories
        plastic_types_dict = {
            "PET": ["bottle", "polyethylene terephthalate", "soft drink bottle"],
            "HDPE": ["high-density polyethylene", "plastic bag", "milk jug"],
            "PVC": ["polyvinyl chloride", "pipe", "vinyl"],
            "LDPE": ["low-density polyethylene", "plastic wrap", "grocery bag"],
            "PP": ["polypropylene", "yogurt container", "straw"],
            "PS": ["polystyrene", "styrofoam", "disposable cup"],
            "Other": ["bioplastics", "unknown plastic"]
        }

        plastic_types = {key: 0 for key in plastic_types_dict.keys()}

        for label in labels:
            if label["Name"] in organic_waste_dict:
                organic_waste += 1
            elif label["Name"] in solid_waste_dict:
                solid_waste += 1
            elif label["Name"] in hazardous_waste_dict:
                hazardous_waste += 1
            else:
                other_waste += 1

            # Check for plastic subcategories
            for plastic_type, keywords in plastic_types_dict.items():
                if any(keyword in label_name for keyword in keywords):
                    plastic_types[plastic_type] += 1

            if label["Name"] not in sorted_waste_items:
                sorted_waste_items.append(label["Name"])

        event[0]["sorted_waste"] = sorted_waste_items
        event[0]["organic_waste"] = organic_waste
        event[0]["solid_waste"] = solid_waste
        event[0]["hazardous_waste"] = hazardous_waste
        event[0]["other_waste"] = other_waste
        event[0]["plastic_types"] = plastic_types
        event[0]["event_date"] = get_event_date(event)
        print(event)
    else:
        sorted_waste_items = []
        event[0]["sorted_waste"] = sorted_waste_items
        event[0]["organic_waste"] = 0
        event[0]["solid_waste"] = 0
        event[0]["hazardous_waste"] = 0
        event[0]["other_waste"] = 0
        event[0]["plastic_types"] = {}
        event[0]["event_date"] = get_event_date(event)
    return event
