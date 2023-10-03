from typing import Optional


def dict_comparsion(
    dict_a: dict,
    dict_b: dict,
    exclude_keys: Optional[list] = None,
):
    """
    Compare two dictionaries

    Args:
        dict_a (dict): dictionary
        dict_b (dict): dictionary
        exclude_keys (list, optional):
            list of keys to exclude from comparison. Defaults to None.
        defaults for their specifc type.

    Raises:
        AssertionError: if the two dictionaries are not equal
    """
    exclude_keys = exclude_keys or []
    for key, value in dict_a.items():
        if key in exclude_keys:
            continue
        assert value == dict_b[key]
