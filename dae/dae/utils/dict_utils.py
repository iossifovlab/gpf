from copy import deepcopy


def recursive_dict_update(input_dict: dict, updater_dict: dict) -> dict:
    """Recursively update a dictionary with another dictionary."""
    # This method cannot handle nested dictionaries
    # that hold a reference to the dictionary that
    # contains them. If such a dictionary is given
    # to this function, it will reach the maximum
    # recursion depth.

    result_dict = deepcopy(input_dict)
    for key, val in updater_dict.items():
        if key in result_dict and isinstance(val, dict):
            assert isinstance(result_dict[key], dict), result_dict[key]
            result_dict[key] = recursive_dict_update(
                result_dict[key], updater_dict[key],
            )
        else:
            result_dict[key] = updater_dict[key]
    return result_dict


def recursive_dict_update_inplace(
    input_dict: dict, updater_dict: dict,
) -> None:
    """Recursively update a dictionary with another dictionary."""
    # This method cannot handle nested dictionaries
    # that hold a reference to the dictionary that
    # contains them. If such a dictionary is given
    # to this function, it will reach the maximum
    # recursion depth.

    for key, val in updater_dict.items():
        if key in input_dict and isinstance(val, dict):
            assert isinstance(input_dict[key], dict), input_dict[key]
            recursive_dict_update_inplace(
                input_dict[key], updater_dict[key],
            )
        else:
            input_dict[key] = updater_dict[key]
