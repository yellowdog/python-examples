"""
Check that configuration values are the types we expect.
If not, raise an Exception.
"""


def _type(type_) -> str:
    if "int" in f"{type_}":
        return "Integer"
    if "float" in f"{type_}":
        return "Float"
    if "bool" in f"{type_}":
        return "Boolean"
    if "str" in f"{type_}":
        return "String"
    if "list" in f"{type_}":
        return "List"
    if "dict" in f"{type_}":
        return "Dict"
    raise Exception(f"Unhandled type '{type_}'")


def _check(thing, type_):
    """
    If None is passed in, just return None.
    """
    if thing is None:
        return thing

    # Bool is a subtype of int, so test for exact match in that case
    is_required_type = (
        type(thing) == type_ if type_ is bool else isinstance(thing, type_)
    )
    if not is_required_type:
        raise Exception(f"Property value '{thing}' should be of type '{_type(type_)}'")
    return thing


def check_int(thing):
    return _check(thing, int)


def check_float(thing):
    return _check(thing, float)


def check_float_or_int(thing):
    """
    For values that should be Floats but for which an Integer is acceptable.
    """
    if thing is None:
        return thing
    try:
        return _check(thing, float)
    except:
        try:
            return _check(thing, int)
        except:
            raise Exception(
                f"Property value '{thing}' should be of type 'Float' or 'Integer'"
            )


def check_bool(thing):
    return _check(thing, bool)


def check_str(thing):
    return _check(thing, str)


def check_list(thing):
    return _check(thing, list)


def check_dict(thing):
    return _check(thing, dict)
