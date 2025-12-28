import boto3
from datetime import datetime, UTC


def lambda_handler(event, context):
    rekognition = boto3.client("rekognition")
    sns = boto3.client("sns")

    if "Records" not in event:
        print("Error: Invalid event structure")
        return

    # Threat labels with minimum confidence thresholds
    THREATS = {
        "Weapon": 85, "Gun": 85, "Handgun": 85, "Rifle": 85, "Knife": 80,
        "Fire": 90, "Flame": 90, "Explosion": 90, "Smoke": 80,
        "Violence": 85, "Fighting": 85, "Blood": 85,
        "Car Crash": 85, "Collision": 85, "Vehicle Accident": 85,
        "Injury": 80, "Wound": 80, "Emergency": 80, "Ambulance": 75,
    }

    # REPLACE THIS WITH YOUR OWN SNS TOPIC ARN
    SNS_TOPIC_ARN = "arn:aws:sns:REGION:ACCOUNT_ID:TOPIC_NAME"

    for record in event["Records"]:
        bucket_name = record["s3"]["bucket"]["name"]
        file_name = record["s3"]["object"]["key"]

        print(f"Processing file: s3://{bucket_name}/{file_name}")

        response = rekognition.detect_labels(
            Image={
                "S3Object": {
                    "Bucket": bucket_name,
                    "Name": file_name,
                }
            },
            MaxLabels=15,
            MinConfidence=60,
        )

        detected_threats = {}

        for label in response["Labels"]:
            name = label["Name"]
            confidence = label["Confidence"]

            if name in THREATS and confidence >= THREATS[name]:
                detected_threats[name] = round(confidence, 1)

        if detected_threats:
            event_time = datetime.now(UTC)

            message = (
                "INCIDENT DETECTED\n"
                f"Time: {event_time.isoformat()}\n"
                f"File: s3://{bucket_name}/{file_name}\n"
                f"Detected Threats: {detected_threats}"
            )

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="[ALERT] High-Risk Incident",
                Message=message,
            )

            print(f"Alert sent at {event_time.isoformat()}")
        else:
            print("Status: Clean")