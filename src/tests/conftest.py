import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_context():
    context = MagicMock()
    context.log_stream_name = "test-log-stream"
    return context

@pytest.fixture
def create_event():
    return {
        "RequestType": "Create",
        "ResponseURL": "https://cloudformation-custom-resource-response-test.example.com/",
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/1234",
        "RequestId": "test-request-1234",
        "ResourceType": "Custom::SubnetDetails",
        "LogicalResourceId": "SubnetDetails",
        "ResourceProperties": {
            "SubnetId": "subnet-12345678"
        }
    }

@pytest.fixture
def delete_event():
    return {
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

@pytest.fixture
def mock_subnet_response():
    return {
        "Subnets": [
            {
                "SubnetId": "subnet-12345678",
                "VpcId": "vpc-12345678",
                "CidrBlock": "10.0.0.0/24",
                "AvailabilityZone": "us-east-1a"
            }
        ]
    }

@pytest.fixture
def mock_route_table_response():
    return {
        "RouteTables": [
            {
                "RouteTableId": "rtb-12345678",
                "VpcId": "vpc-12345678",
                "Associations": [
                    {
                        "Main": True,
                        "RouteTableId": "rtb-12345678",
                        "SubnetId": "subnet-12345678"
                    }
                ]
            }
        ]
    }
