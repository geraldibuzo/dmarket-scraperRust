# exceptions.py
class AuthenticationError(Exception):
    pass


class NavigationError(Exception):
    pass


class DataFetchError(Exception):  # Add this missing class
    """Exception raised for errors during data fetching."""

    pass
