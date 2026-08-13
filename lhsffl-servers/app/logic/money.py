"""
Money helpers for UDFA budgets and bids.

Dollar amounts are stored as DECIMAL(7,2) and handled as Decimal everywhere, never float:
settle_bids() detects a tie with an exact `==` comparison before falling through to waiver_order,
so binary float error would silently change who wins a player.

Values can reach these helpers as Decimal (MySQL), float (the SQLite round-trip in tests), int
(literals in fixtures and seeding), or str (JSON request bodies), so everything is normalised
through str() — Decimal(0.1) keeps the binary expansion, Decimal('0.1') does not.
"""
from decimal import Decimal

CENT = Decimal('0.01')
ZERO = Decimal('0.00')


def to_money(value):
    """Coerce any numeric representation to a 2dp Decimal."""
    if isinstance(value, Decimal):
        return value.quantize(CENT)
    return Decimal(str(value)).quantize(CENT)


def cents_of(value):
    """The fractional part of an amount, as a 2dp Decimal. $110.50 -> Decimal('0.50')."""
    return to_money(value) % 1


def format_money(value):
    """Render for user-facing error messages: $110.50 -> '110.50', $100 -> '100'."""
    amount = to_money(value)
    return f'{amount:.0f}' if amount % 1 == ZERO else f'{amount:.2f}'
