# pylint: disable=W0621,C0114,C0116,W0212,W0613
import uuid

import pytest

from rest_client.rest_client import (
    GPFBasicAuth,
    GPFConfidentialClient,
    RESTClient,
)


@pytest.fixture(
    scope="module",
    params=["basic", "oauth2_confidential_client"],
)
def admin_client(
    request: pytest.FixtureRequest,
) -> RESTClient:
    if request.param == "basic":
        basic_session = GPFBasicAuth(
            base_url="http://resttest:21011",
            username="admin@iossifovlab.com",
            password="secret",  # noqa: S106
        )
        client = RESTClient(basic_session)
        client.login()
        return client

    if request.param == "oauth2_confidential_client":
        confidential_session = GPFConfidentialClient(
            base_url="http://resttest:21011",
            client_id="resttest1",
            client_secret="secret",  # noqa: S106
            redirect_uri="http://resttest:21011/login",
        )

        client = RESTClient(confidential_session)
        client.login()
        return client
    raise ValueError(f"Unknown request parameter: {request.param}")


@pytest.fixture(
    scope="module",
    params=["basic", "oauth2_confidential_client"],
)
def user_client(
    request: pytest.FixtureRequest,
) -> RESTClient:
    if request.param == "basic":
        basic_session = GPFBasicAuth(
            base_url="http://resttest:21011",
            username="research@iossifovlab.com",
            password="secret",  # noqa: S106
        )
        client = RESTClient(basic_session)
        client.login()
        return client

    if request.param == "oauth2_confidential_client":
        confidential_session = GPFConfidentialClient(
            base_url="http://resttest:21011",
            client_id="resttest2",
            client_secret="secret",  # noqa: S106
            redirect_uri="http://resttest:21011/login",
        )

        client = RESTClient(confidential_session)
        client.login()
        return client
    raise ValueError(f"Unknown request parameter: {request.param}")


def test_create_user(admin_client: RESTClient) -> None:
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"

    result = admin_client.create_user(username, name)
    assert result["name"] == name
    assert result["email"] == username


def test_double_create_user_fail(
    admin_client: RESTClient,
) -> None:
    """Test creating a user."""
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"

    new_user = admin_client.create_user(username, name)
    assert new_user["email"] == username

    with pytest.raises(OSError, match=f"Create user <{username}> failed:"):
        admin_client.create_user(username, name)


def create_new_user(admin_client: RESTClient) -> dict:
    """Create a new user."""
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"

    result = admin_client.create_user(username, name)
    assert result["name"] == name
    assert result["email"] == username
    return result


def test_update_user_groups(
    admin_client: RESTClient,
) -> None:
    """Test updating user groups."""
    user_id = create_new_user(admin_client)["id"]
    user = admin_client.get_user(user_id)

    user["groups"].extend(["test_group_1", "test_group_2"])
    email = user.pop("email")

    result = admin_client.update_user(user_id, user)
    assert set(result["groups"]) == {
        "any_user", email, "test_group_1", "test_group_2",
    }


def test_update_user_name(
    admin_client: RESTClient,
) -> None:
    """Test updating user groups."""
    user_id = create_new_user(admin_client)["id"]
    user = admin_client.get_user(user_id)
    email = user.pop("email")

    user["name"] = "New Test User Name"
    result = admin_client.update_user(user_id, user)

    assert result["id"] == user_id
    assert result["name"] == "New Test User Name"

    result = admin_client.get_user(user_id)
    assert result["id"] == user_id
    assert result["name"] == "New Test User Name"
    assert result["email"] == email


def test_get_dataset(
    admin_client: RESTClient,
) -> None:
    """Test getting datasets."""
    datasets = admin_client.get_all_datasets()
    assert len(datasets) > 0


def test_get_all_groups(
    admin_client: RESTClient,
) -> None:
    """Test getting all groups."""
    groups = admin_client.get_all_groups()
    assert len(groups) > 0


def test_get_a_group(
    admin_client: RESTClient,
) -> None:
    """Test getting a group."""
    groups = admin_client.get_all_groups()
    assert len(groups) > 0

    group_name = groups[0]["name"]
    group = admin_client.get_group(group_name)

    assert group["name"] == group_name


def test_add_group_to_a_dataset(
    admin_client: RESTClient,
) -> None:
    """Test adding a group to a dataset."""
    datasets = admin_client.get_all_datasets()
    assert len(datasets) > 0

    dataset_id = datasets[0]["id"]
    dataset = admin_client.get_dataset(dataset_id)

    test_group_name = f"test_group_{uuid.uuid4()}"
    assert test_group_name not in {g["name"] for g in dataset["groups"]}

    admin_client.grant_permission(dataset_id, test_group_name)

    dataset = admin_client.get_dataset(dataset_id)
    assert test_group_name in {g["name"] for g in dataset["groups"]}


def test_add_group_to_a_dataset_twice(
    admin_client: RESTClient,
) -> None:
    datasets = admin_client.get_all_datasets()
    assert len(datasets) > 0

    dataset_id = datasets[0]["id"]
    dataset = admin_client.get_dataset(dataset_id)

    test_group_name = f"test_group_{uuid.uuid4()}"
    assert test_group_name not in {g["name"] for g in dataset["groups"]}

    admin_client.grant_permission(dataset_id, test_group_name)
    admin_client.grant_permission(dataset_id, test_group_name)

    dataset = admin_client.get_dataset(dataset_id)
    assert test_group_name in {g["name"] for g in dataset["groups"]}


def test_remove_group_from_a_dataset(
    admin_client: RESTClient,
) -> None:
    """Test removing a group from a dataset."""
    datasets = admin_client.get_all_datasets()
    assert len(datasets) > 0

    dataset_id = datasets[0]["id"]
    dataset = admin_client.get_dataset(dataset_id)

    test_group_name = f"test_group_{uuid.uuid4()}"
    assert test_group_name not in dataset["groups"]
    admin_client.grant_permission(dataset_id, test_group_name)

    dataset = admin_client.get_dataset(dataset_id)
    assert test_group_name in {g["name"] for g in dataset["groups"]}

    group = admin_client.get_group(test_group_name)

    admin_client.revoke_permission(dataset_id, group["id"])
    dataset = admin_client.get_dataset(dataset_id)

    assert test_group_name not in {g["name"] for g in dataset["groups"]}


def test_get_all_users_by_non_admin_user(
    user_client: RESTClient,
) -> None:
    """Test getting all users by non-admin user."""
    with pytest.raises(
            OSError,
            match="Get all users failed: You do not have permission"):
        user_client.get_all_users()


def test_get_all_users(admin_client: RESTClient) -> None:
    """Test authenticate simple."""
    result = admin_client.get_all_users()
    assert result is not None
    assert len(result) > 0


def test_get_a_user_by_non_admin_user(
    admin_client: RESTClient,
    user_client: RESTClient,
) -> None:
    """Test getting a user by non-admin user."""
    all_users = admin_client.get_all_users()
    assert len(all_users) > 0
    user = all_users[0]

    with pytest.raises(
            OSError, match="Get user failed: You do not have permission"):
        user_client.get_user(user["id"])


def test_create_a_user_by_non_admin_user(
    user_client: RESTClient,
) -> None:
    """Test getting a user by non-admin user."""
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    with pytest.raises(
            OSError,
            match=r"Create user .* failed: You do not have permission"):
        user_client.create_user(username, "Test User")


def test_update_a_user_by_non_admin_user(
    admin_client: RESTClient,
    user_client: RESTClient,
) -> None:
    """Test updating a user by non-admin user."""
    all_users = admin_client.get_all_users()
    assert len(all_users) > 0

    user = all_users[0]
    user_id = user["id"]
    del user["email"]
    user["name"] = "Updated Test User"

    with pytest.raises(
            OSError,
            match="Update user failed: You do not have permission"):
        user_client.update_user(user_id, user)


def test_get_all_groups_by_non_admin_user(
    user_client: RESTClient,
) -> None:
    """Test getting all groups by non admin user."""
    with pytest.raises(
            OSError,
            match="Get all groups failed: You do not have permission"):
        user_client.get_all_groups()


def test_get_a_group_by_non_admin_user(
    admin_client: RESTClient,
    user_client: RESTClient,
) -> None:
    """Test getting a group."""
    groups = admin_client.get_all_groups()
    assert len(groups) > 0

    group_name = groups[0]["name"]
    with pytest.raises(
            OSError,
            match=r"Get group .* failed: You do not have permission"):
        user_client.get_group(group_name)


def test_add_group_to_a_dataset_by_non_admin_user(
    user_client: RESTClient,
) -> None:
    """Test adding a group to a dataset."""
    datasets = user_client.get_all_datasets()
    assert len(datasets) > 0

    dataset_id = datasets[0]["id"]
    dataset = user_client.get_dataset(dataset_id)

    test_group_name = f"test_group_{uuid.uuid4()}"
    assert test_group_name not in {g["name"] for g in dataset["groups"]}

    with pytest.raises(
            OSError,
            match="Grant permission failed"):
        user_client.grant_permission(dataset_id, test_group_name)

    dataset = user_client.get_dataset(dataset_id)
    assert test_group_name not in {g["name"] for g in dataset["groups"]}


def test_remove_group_from_a_dataset_by_non_admin_user(
    admin_client: RESTClient,
    user_client: RESTClient,
) -> None:
    """Test removing a group from a dataset."""
    datasets = admin_client.get_all_datasets()
    assert len(datasets) > 0

    dataset_id = datasets[0]["id"]
    dataset = admin_client.get_dataset(dataset_id)

    test_group_name = f"test_group_{uuid.uuid4()}"
    assert test_group_name not in dataset["groups"]
    admin_client.grant_permission(dataset_id, test_group_name)

    dataset = admin_client.get_dataset(dataset_id)
    assert test_group_name in {g["name"] for g in dataset["groups"]}

    group = admin_client.get_group(test_group_name)

    with pytest.raises(
            OSError,
            match="Revoke permission failed"):
        user_client.revoke_permission(dataset_id, group["id"])

    dataset = admin_client.get_dataset(dataset_id)
    assert test_group_name in {g["name"] for g in dataset["groups"]}
