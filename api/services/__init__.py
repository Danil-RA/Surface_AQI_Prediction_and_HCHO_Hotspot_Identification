class MissingDataError(Exception):
    """Raised when an external data source is genuinely missing required features."""
    def __init__(self, missing_data: list, available_data: list):
        self.missing_data = missing_data
        self.available_data = available_data
        super().__init__("Environmental data is unavailable.")

class VWSUnavailableError(Exception):
    """Raised because VWS implementation is pending."""
    pass
