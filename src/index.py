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


def get_subnet_properties(event):
    ec2 = boto3.client("ec2")
    resource_properties = event.get("ResourceProperties")
    subnet_id = resource_properties.get("SubnetId")
    subnet_response = ec2.describe_subnets(SubnetIds=[subnet_id])
    subnets = subnet_response.get("Subnets", [])
    subnet = None
    if subnets:
        subnet = subnets[0]
        route_table_response = ec2.describe_route_tables(
            Filters=[{"Name": "association.subnet-id", "Values": [subnet_id]}]
        )
        route_tables = route_table_response.get("RouteTables", [])
        main_route_table = None
        for route_table in route_tables:
            for association in route_table.get("Associations", []):
                if association.get("Main"):
                    main_route_table = route_table
                    break
            if main_route_table:
                break
        subnet["RouteTable"] = main_route_table.get("RouteTableId")
    return subnet


def handler(event, context):
    print(json.dumps(event, indent=2))
    try:
        if event.get("RequestType") == "Delete":
            send_response(event, context, "SUCCESS")
            return
        subnet_properties = get_subnet_properties(event)
        send_response(event, context, "SUCCESS", subnet_properties)
    except Exception as e:
        send_response(event, context, "FAILED")
        raise e
