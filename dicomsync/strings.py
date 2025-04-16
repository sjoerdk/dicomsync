"""Functions that work with strings"""

from slugify import slugify


def make_slug(string_in: str) -> str:
    """Make sure the string is a valid slug, usable in a URL or path.
     Uses underscore seperator.

    Returns
    -------
    str Input unchanged

    Raises
    ------
    ValueError
        If string_in is not a valid slug
    """
    response: str = slugify(string_in, separator="_", lowercase=True)

    return response


def assert_is_valid_slug(string_in):
    """Asserts alphanumeric and undercore. Raises ValueError if not"""

    if not isinstance(string_in, str) or not all(
        c.isalnum() or c == "_" for c in string_in
    ):
        raise ValueError(
            f"Invalid slug: '{string_in}' Only alphanumeric and " f"underscore allowed"
        )
