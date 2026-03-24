CURRENCY_SYMBOLS = {
    "USD": "$",
    "KRW": "₩",
    "JPY": "¥",
    "EUR": "€",
    "GBP": "£",
    "CNY": "¥",
    "HKD": "HK$",
    "INR": "₹",
    "CAD": "C$",
    "AUD": "A$",
    "CHF": "CHF ",
    "SGD": "S$",
    "TWD": "NT$",
    "BRL": "R$",
    "MXN": "MX$",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
}


def format_large_number(value: float | int | None, currency: str = "USD") -> str | None:
    if value is None:
        return None
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    abs_value = abs(value)
    if abs_value >= 1e12:
        formatted = f"{value / 1e12:.1f}T"
    elif abs_value >= 1e9:
        formatted = f"{value / 1e9:.1f}B"
    elif abs_value >= 1e6:
        formatted = f"{value / 1e6:.1f}M"
    elif abs_value >= 1e3:
        formatted = f"{value / 1e3:.1f}K"
    else:
        formatted = f"{value:.2f}"
    return f"{symbol}{formatted}"


def format_currency(value: float | int | None, currency: str = "USD") -> str | None:
    if value is None:
        return None
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    return f"{symbol}{value:,.2f}"


def format_percentage(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value * 100:.2f}%"
