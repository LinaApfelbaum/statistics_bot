from dataclasses import dataclass

@dataclass(frozen=True)
class Buttons:
    ADD_SPEND: str = "Add spend"
    CHANGE_CURRENCY: str = "Change currency"
    LAST_ENTRIES: str = "Last entries"
    CANCEL: str = "Cancel"

    @classmethod
    def all(cls):
        return [
            cls.ADD_SPEND,
            cls.CHANGE_CURRENCY,
            cls.LAST_ENTRIES,
            cls.CANCEL
        ]


@dataclass(frozen=True)
class SupportedCurrencies:
    RSD: str = "RSD"
    USD: str = "USD"
    EUR: str = "EUR"
    GBP: str = "GBP"
    RUB: str = "RUB"

    @classmethod
    def all(cls):
        return [
            cls.RSD,
            cls.USD,
            cls.EUR,
            cls.GBP,
            cls.RUB
        ]
