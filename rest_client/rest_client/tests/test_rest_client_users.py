# pylint: disable=W0621,C0114,C0116,W0212,W0613
import time
import uuid
from typing import cast

import pytest

from rest_client.mailhog_client import (
    MailhogClient,
)
from rest_client.rest_client import (
    RESTClient,
)


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


def test_initiate_forgotten_password(
    admin_client: RESTClient,
) -> None:
    """Test initiating password reset."""
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    admin_client.create_user(username, "Test User")

    admin_client.initiate_forgotten_password(username)


def test_initiate_password_reset_old(
    admin_client: RESTClient,
    mail_client: MailhogClient,
) -> None:
    """Test deprecated initiating password reset."""
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    user = admin_client.create_user(username, "Test User")
    user_id = user["id"]
    mail_client.delete_all_messages()
    time.sleep(0.5)

    admin_client.initiate_password_reset_old(user_id)

    time.sleep(0.5)
    message = mail_client.find_message_to_user(username)
    print(message)

    assert mail_client.get_email_to(message) == username


def test_initiate_forgotten_password_for_non_existing_user(
    admin_client: RESTClient,
) -> None:
    """Test initiating password reset."""
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    admin_client.initiate_forgotten_password(username)


def test_initiate_reset_password_old_for_non_existing_user(
    admin_client: RESTClient,
    mail_client: MailhogClient,
) -> None:
    """Test initiating password reset."""
    mail_client.delete_all_messages()
    time.sleep(0.5)

    with pytest.raises(OSError, match="Initiate old password reset failed"):
        admin_client.initiate_password_reset_old(-1)

    time.sleep(0.5)
    all_messages = mail_client.get_all_messages()

    assert cast(int, all_messages["count"]) == 0


def test_initiate_forgotten_password_by_anonymous_user(
    admin_client: RESTClient,
    annon_client: RESTClient,
) -> None:
    """Test initiating password reset."""
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    admin_client.create_user(username, "Test User")

    annon_client.initiate_forgotten_password(username)


def test_initiate_reset_password_old_by_anonymous_user(
    admin_client: RESTClient,
    annon_client: RESTClient,
    mail_client: MailhogClient,
) -> None:
    """Test initiating password reset."""
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    user = admin_client.create_user(username, "Test User")
    mail_client.delete_all_messages()
    time.sleep(0.5)

    with pytest.raises(OSError, match="Initiate old password reset failed"):
        annon_client.initiate_password_reset_old(user["id"])

    time.sleep(0.5)
    all_messages = mail_client.get_all_messages()
    assert all_messages["count"] == 0


def test_admin_user_logout(
    admin_client: RESTClient,
) -> None:
    """Test admin user logout."""
    users = admin_client.get_all_users()
    assert len(users) > 0

    admin_client.logout()

    with pytest.raises(
            OSError,
            match="Get all users failed: "):
        admin_client.get_all_users()


def test_search_user(
    admin_client: RESTClient,
) -> None:
    """Test searching users."""
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    admin_client.create_user(username, name)

    result = admin_client.search_users(username)
    assert len(result) == 1
    assert result[0]["name"] == name
    assert result[0]["email"] == username


def test_create_and_reset_password(
    admin_client: RESTClient,
    mail_client: MailhogClient,
) -> None:
    """Test create user and password reset."""
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    user = admin_client.create_user(username, name)

    admin_client.initiate_password_reset_old(user["id"])

    result = mail_client.find_message_to_user(username)
    assert mail_client.get_email_to(result) == username


def test_create_update_and_reset_password(
    admin_client: RESTClient,
    mail_client: MailhogClient,
) -> None:
    """Test create user, update it and password reset."""
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    user = admin_client.create_user(username, name)
    user_id = user["id"]

    user["groups"].extend(["test_group_1", "test_group_2"])
    user.pop("email")
    user["name"] = "Updated Test User"
    admin_client.update_user(user_id, user)

    admin_client.initiate_password_reset_old(user["id"])

    result = mail_client.find_message_to_user(username)
    assert mail_client.get_email_to(result) == username


def test_create_update_and_reset_password_10(
    admin_client: RESTClient,
) -> None:
    """Test create 10 users, update them and initiate password reset."""
    users = []
    for _ in range(10):
        name = "Test User"
        username = f"test_{uuid.uuid4()}@iossifovlab.com"
        user = admin_client.create_user(username, name)

        user["groups"].extend(["test_group_1", "test_group_2"])
        user.pop("email")
        user["name"] = "Updated Test User"
        users.append(user)

        admin_client.update_user(user["id"], user)

        admin_client.initiate_password_reset_old(user["id"])


GROUPS = [
    "SD_ACS2014_liftover",
    "SD_AGRE_WG38_859_DENOVO",
    "SD_Chung2015CHD_liftover",
    "SD_DDD2017_liftover",
    "SD_EichlerTG2012_liftover",
    "SD_EichlerWE2012_liftover",
    "SD_Epi4KWE2013_liftover",
    "SD_GulsunerSchWE2013_liftover",
    "SD_Helbig2016_liftover",
    "SD_IossifovWE2014_liftover",
    "SD_KarayiorgouWE2012_liftover",
    "SD_Krumm2015_SNVindel_liftover",
    "SD_Lelieveld2016_liftover",
    "SD_McCarthy2014_liftover",
    "SD_ODonovanWE2014_liftover",
    "SD_ORoakTG2014_SSC_liftover",
    "SD_ORoakTG2014_TASC_liftover",
    "SD_Rauch2012_liftover",
    "SD_SFARI_SSC_WGS_CSHL_DENOVO",
    "SD_Takata2018_liftover",
    "SD_Turner2017_liftover",
    "SD_VissersWE2012_liftover",
    "SD_Werling2018_liftover",
    "SD_Yuen2017_liftover",
    "SD_iWES_v1_1_genotypes_DENOVO",
    "iWES_DNM_v1_1",
    "iWES_v1_1",
    "iWES_v2",
    "iWGS_v1_1",
]


def test_create_reset(
    admin_client: RESTClient,
) -> None:
    name = "Test User"
    username = f"test_{uuid.uuid4()}@iossifovlab.com"
    user = admin_client.create_user(username, name, GROUPS)

    admin_client.initiate_password_reset_old(user["id"])
