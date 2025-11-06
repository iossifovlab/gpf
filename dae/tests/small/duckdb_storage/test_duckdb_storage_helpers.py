# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest
import pytest_mock
from dae.duckdb_storage.duckdb_storage_helpers import (
    create_s3_secret_clause,
)


@pytest.mark.parametrize(
    "key_id,secret,region,endpoint,expected_clause",
    [
        ("my_key", "my_secret", "us-west-2", None,
         textwrap.dedent("""
            create secret (
                type s3,
                key_id 'my_key',
                secret 'my_secret',
                region 'us-west-2'
            );
            """)),
        ("my_key", "my_secret", None, "http://localhost:9000",
         textwrap.dedent("""
            create secret (
                type s3,
                key_id 'my_key',
                secret 'my_secret',
                endpoint 'localhost:9000',
                use_ssl 'true',
                url_style 'path',
                region 'us-east-1'
            );
            """)),
        ("my_key", "my_secret", "us-east-1",
         "s3express-use1-az5.us-east-1.amazonaws.com",
         textwrap.dedent("""
            create secret (
                type s3,
                key_id 'my_key',
                secret 'my_secret',
                endpoint 's3express-use1-az5.us-east-1.amazonaws.com',
                use_ssl 'true',
                region 'us-east-1'
            );
            """)),
    ],
)
def test_create_s3_secret_clause(
    mocker: pytest_mock.MockerFixture,
    key_id: str | None,
    secret: str | None,
    region: str | None,
    endpoint: str | None,
    expected_clause: str,
) -> None:
    mocker.patch("os.environ", {
        "AWS_ACCESS_KEY_ID": key_id,
        "AWS_SECRET_ACCESS_KEY": secret,
        "AWS_REGION": region,
    })
    clause = create_s3_secret_clause(
        storage_id="test_storage",
        endpoint_url=endpoint,
    )
    assert clause.strip() == expected_clause.strip()
