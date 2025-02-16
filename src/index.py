import json
import boto3
import urllib3


def send_response(event, context, response_status, response_data=None):
    response_body = {
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: "
        + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event.get("StackId"),
        "RequestId": event.get("RequestId"),
        "LogicalResourceId": event.get("LogicalResourceId"),
        "Data": response_data,
    }
    response_body = json.dumps(response_body)
    headers = {"Content-Type": "", "Content-Length": str(len(response_body))}
    response_url = event.get("ResponseURL")
    http = urllib3.PoolManager()
    http.request("PUT", response_url, body=response_body, headers=headers)


def get_subnet_cidr_block(event):
    subnet_id = event.get("ResourceProperties").get("SubnetId")
    ec2 = boto3.client("ec2")
    subnet = ec2.describe_subnets(SubnetIds=[subnet_id])
    cidr_block = subnet.get("Subnets")[0].get("CidrBlock")
    return cidr_block


def handler(event, context):
    print(json.dumps(event, indent=2))
    try:
        if event.get("RequestType") == "Delete":
            send_response(event, context, "SUCCESS")
            return
        cidr_block = get_subnet_cidr_block(event)
        response_data = {"CidrBlock": cidr_block}
        send_response(event, context, "SUCCESS", response_data)
    except Exception as e:
        send_response(event, context, "FAILED")
        raise e
