import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib")))

from storage_writer import write_to_aws, write_to_local

def test_write_to_local(mocker):
    """
    Tests that the local writer creates directories and writes a file.
    """
    # Mock the file system calls
    mocker.patch("os.makedirs")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    secrets = {"storage": "local", "local_output_directory": "/test/output"}
    test_metrics = {"test_collection": [{"metric": "value"}]}
    
    write_to_local(secrets, "test-id", "test-host", "2025-07-22T18:00:00Z", **test_metrics)

    # Assert that makedirs was called to create the directory structure
    assert os.makedirs.call_count == 1
    
    # Assert that open was called to write the file
    mock_open.assert_called_once()
    # Check that the path contains the expected components
    written_path = mock_open.call_args[0][0]
    assert "/test/output" in written_path
    assert "test_collection-metrics" in written_path
    assert "test-host_test_collection_test-id.json.gz" in written_path


def test_write_to_aws(mocker):
    """
    Tests that the AWS S3 writer is called with the correct parameters.
    """
    # Mock the boto3 client
    mock_s3_client = mocker.Mock()
    mocker.patch("boto3.client", return_value=mock_s3_client)

    secrets = {
        "storage": "aws",
        "aws_access_key": "fake",
        "aws_secret_key": "fake",
        "s3_bucket": "test-bucket"
    }
    test_metrics = {"aws_test_collection": [{"metric": "aws_value"}]}

    write_to_aws(secrets, "aws-id", "aws-host", "2025-07-22T18:00:00Z", **test_metrics)

    # Assert that the S3 client's put_object method was called
    mock_s3_client.put_object.assert_called_once()
    
    # Check the arguments passed to put_object
    kwargs = mock_s3_client.put_object.call_args[1]
    assert kwargs["Bucket"] == "test-bucket"
    assert "aws_test_collection-metrics" in kwargs["Key"]
    assert "aws-host_aws_test_collection_aws-id.json.gz" in kwargs["Key"]
    assert isinstance(kwargs["Body"], bytes) # Check that the body is compressed bytes

