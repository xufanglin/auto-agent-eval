import re


class ValidationError(Exception):
    pass


class URLValidator:
    """Validate URLs. Simplified from django.core.validators."""

    schemes = ["http", "https", "ftp", "ftps"]

    # BUG: host pattern does not allow bracketed IPv6 addresses
    host_re = (
        r"("
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
        r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)"
        r"|localhost"
        r")"
    )

    scheme_re = r"(?:" + "|".join(schemes) + r")://"
    port_re = r"(?::\d{2,5})?"
    path_re = r"(?:[/?#][^\s]*)?"

    regex = re.compile(
        r"^" + scheme_re + host_re + port_re + path_re + r"$",
        re.IGNORECASE,
    )

    def __call__(self, value):
        if not self.regex.match(value):
            raise ValidationError(f"Enter a valid URL: {value}")
