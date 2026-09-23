class MissingDataError(Exception):
    """Raised when an external data source is genuinely missing required features."""
    def __init__(self, feature: str, source: str, message: str = None):
        self.feature = feature
        self.source = source
        self.message = message or f"Feature '{feature}' is missing from {source}."
        super().__init__(self.message)

class VWSUnavailableError(Exception):
    """Raised because VWS implementation is pending."""
    pass
