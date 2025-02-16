import json
import pytest
from moto import mock_ec2
import boto3
from ..index import handler

@mock_ec2
def test_full_integration(mock_context):
    """Test full integration with mocked AWS services"""
    # Set up mock AWS resources
    ec2 = boto3.client("ec2", region_name="us-east-1")
    
    # Create VPC
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    vpc_id = vpc["Vpc"]["VpcId"]
    
    # Create Subnet
    subnet = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock="10.0.1.0/24",
        AvailabilityZone="us-east-1a"
    )
    subnet_id = subnet["Subnet"]["SubnetId"]
    
    # Create and associate Route Table
    route_table = ec2.create_route_table(VpcId=vpc_id)
    route_table_id = route_table["RouteTable"]["RouteTableId"]
    
    ec2.associate_route_table(
        RouteTableId=route_table_id,
        SubnetId=subnet_id
    )
    
    # Create CloudFormation event
    event = {
        "RequestType": "Create",
        "ResponseURL": "https://cloudformation-custom-resource-response-test.example.com/",
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/1234",
        "RequestId": "test-request-1234",
        "ResourceType": "Custom::SubnetDetails",
        "LogicalResourceId": "SubnetDetails",
        "ResourceProperties": {
            "SubnetId": subnet_id
        }
    }
    
    # Test handler with integration environment
    response_data = None
    
    def mock_send_response(_, __, ___, data):
        nonlocal response_data
        response_data = data
    
    # Patch the send_response function to capture the response data
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.index.send_response", mock_send_response)
        handler(event, mock_context)
    
    # Verify response data
    assert response_data is not None
    assert response_data["SubnetId"] == subnet_id
    assert response_data["VpcId"] == vpc_id
    assert response_data["CidrBlock"] == "10.0.1.0/24"
    assert response_data["AvailabilityZone"] == "us-east-1a"
    assert response_data["RouteTable"] == route_table_id

@mock_ec2
def test_integration_no_route_table(mock_context):
    """Test integration when subnet has no route table"""
    # Set up mock AWS resources
    ec2 = boto3.client("ec2", region_name="us-east-1")
    
    # Create VPC and Subnet without Route Table
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    subnet = ec2.create_subnet(
        VpcId=vpc["Vpc"]["VpcId"],
        CidrBlock="10.0.1.0/24",
        AvailabilityZone="us-east-1a"
    )
    
    event = {
        "RequestType": "Create",
        "ResponseURL": "https://cloudformation-custom-resource-response-test.example.com/",
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/1234",
        "RequestId": "test-request-1234",
        "ResourceType": "Custom::SubnetDetails",
        "LogicalResourceId": "SubnetDetails",
        "ResourceProperties": {
            "SubnetId": subnet["Subnet"]["SubnetId"]
        }
    }
    
    response_data = None
    
    def mock_send_response(_, __, ___, data):
        nonlocal response_data
        response_data = data
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.index.send_response", mock_send_response)
        handler(event, mock_context)
    
    assert response_data is not None
    assert response_data["SubnetId"] == subnet["Subnet"]["SubnetId"]
    assert "RouteTable" not in response_data

@mock_ec2
def test_integration_delete_request(mock_context):
    """Test integration with Delete request type"""
    event = {
        "RequestType": "Delete",
        "ResponseURL": "https://cloudformation-custom-resource-response-test.example.com/",
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/1234",
        "RequestId": "test-request-1234",
        "ResourceType": "Custom::SubnetDetails",
        "LogicalResourceId": "SubnetDetails",
        "ResourceProperties": {
            "SubnetId": "subnet-12345678"
        }
    }
    
    response_status = None
    
    def mock_send_response(_, __, status, ___=None):
        nonlocal response_status
        response_status = status
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.index.send_response", mock_send_response)
        handler(event, mock_context)
    
    assert response_status == "SUCCESS"
