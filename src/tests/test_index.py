import json
import pytest
from unittest.mock import MagicMock, patch
from moto import mock_ec2
import boto3
from ..index import send_response, get_subnet_properties, handler

def test_send_response(mock_context, create_event):
    """Test the send_response function with success status"""
    with patch('urllib3.PoolManager') as mock_pool_manager:
        mock_http = MagicMock()
        mock_pool_manager.return_value = mock_http
        
        response_data = {"test": "data"}
        send_response(create_event, mock_context, "SUCCESS", response_data)
        
        # Verify the HTTP request was made correctly
        mock_http.request.assert_called_once()
        call_args = mock_http.request.call_args[0]
        assert call_args[0] == "PUT"
        assert call_args[1] == create_event["ResponseURL"]
        
        # Verify response body
        sent_body = json.loads(call_args[2])
        assert sent_body["Status"] == "SUCCESS"
        assert sent_body["PhysicalResourceId"] == mock_context.log_stream_name
        assert sent_body["StackId"] == create_event["StackId"]
        assert sent_body["RequestId"] == create_event["RequestId"]
        assert sent_body["LogicalResourceId"] == create_event["LogicalResourceId"]
        assert sent_body["Data"] == response_data

@mock_ec2
def test_get_subnet_properties():
    """Test get_subnet_properties with mocked AWS resources"""
    # Create mock AWS resources
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    subnet = ec2.create_subnet(
        VpcId=vpc["Vpc"]["VpcId"],
        CidrBlock="10.0.1.0/24",
        AvailabilityZone="us-east-1a"
    )
    route_table = ec2.create_route_table(VpcId=vpc["Vpc"]["VpcId"])
    ec2.associate_route_table(
        RouteTableId=route_table["RouteTable"]["RouteTableId"],
        SubnetId=subnet["Subnet"]["SubnetId"]
    )
    
    # Create test event
    event = {
        "ResourceProperties": {
            "SubnetId": subnet["Subnet"]["SubnetId"]
        }
    }
    
    # Test the function
    result = get_subnet_properties(event)
    
    # Verify results
    assert result["SubnetId"] == subnet["Subnet"]["SubnetId"]
    assert result["VpcId"] == vpc["Vpc"]["VpcId"]
    assert result["CidrBlock"] == "10.0.1.0/24"
    assert result["AvailabilityZone"] == "us-east-1a"
    assert "RouteTable" in result

@mock_ec2
def test_get_subnet_properties_no_route_table():
    """Test get_subnet_properties when subnet has no route table"""
    # Create mock AWS resources without route table
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    subnet = ec2.create_subnet(
        VpcId=vpc["Vpc"]["VpcId"],
        CidrBlock="10.0.1.0/24",
        AvailabilityZone="us-east-1a"
    )
    
    event = {
        "ResourceProperties": {
            "SubnetId": subnet["Subnet"]["SubnetId"]
        }
    }
    
    result = get_subnet_properties(event)
    assert result["SubnetId"] == subnet["Subnet"]["SubnetId"]
    assert "RouteTable" not in result

def test_handler_create(mock_context, create_event, mock_subnet_response, mock_route_table_response):
    """Test handler function with Create request"""
    with patch('boto3.client') as mock_boto3_client, \
         patch('src.index.send_response') as mock_send_response:
        
        # Mock EC2 client responses
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = mock_subnet_response
        mock_ec2.describe_route_tables.return_value = mock_route_table_response
        mock_boto3_client.return_value = mock_ec2
        
        # Execute handler
        handler(create_event, mock_context)
        
        # Verify EC2 client calls
        mock_ec2.describe_subnets.assert_called_once_with(
            SubnetIds=[create_event["ResourceProperties"]["SubnetId"]]
        )
        mock_ec2.describe_route_tables.assert_called_once()
        
        # Verify response was sent
        mock_send_response.assert_called_once()
        call_args = mock_send_response.call_args[0]
        assert call_args[0] == create_event
        assert call_args[1] == mock_context
        assert call_args[2] == "SUCCESS"
        assert "RouteTable" in call_args[3]

def test_handler_delete(mock_context, delete_event):
    """Test handler function with Delete request"""
    with patch('src.index.send_response') as mock_send_response:
        handler(delete_event, mock_context)
        
        mock_send_response.assert_called_once_with(
            delete_event,
            mock_context,
            "SUCCESS"
        )

def test_handler_error(mock_context, create_event):
    """Test handler function error handling"""
    with patch('boto3.client') as mock_boto3_client, \
         patch('src.index.send_response') as mock_send_response:
        
        # Mock EC2 client to raise exception
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = Exception("Test error")
        mock_boto3_client.return_value = mock_ec2
        
        # Execute handler and expect exception
        with pytest.raises(Exception):
            handler(create_event, mock_context)
        
        # Verify failed response was sent
        mock_send_response.assert_called_once_with(
            create_event,
            mock_context,
            "FAILED"
        )
