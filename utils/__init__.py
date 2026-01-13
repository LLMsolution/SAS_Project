# SAS Material Supply Analysis - Utils Package

def format_currency(value, prefix="€"):
    """Format currency values compactly (K for thousands, M for millions)"""
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000:
        return f"{sign}{prefix}{abs_value/1_000_000:.1f}M"
    elif abs_value >= 10_000:
        return f"{sign}{prefix}{abs_value/1_000:.0f}K"
    elif abs_value >= 1_000:
        return f"{sign}{prefix}{abs_value/1_000:.1f}K"
    else:
        return f"{sign}{prefix}{abs_value:,.0f}"

def format_number(value):
    """Format large numbers compactly (K for thousands, M for millions)"""
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000:
        return f"{sign}{abs_value/1_000_000:.1f}M"
    elif abs_value >= 10_000:
        return f"{sign}{abs_value/1_000:.0f}K"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value/1_000:.1f}K"
    else:
        return f"{sign}{abs_value:,.0f}"
