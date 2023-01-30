from dataclasses import dataclass, field
from typing import Optional

import algosdk
from algosdk import transaction

from .utils import get_selector, sp_fee

INCREASE_OPCODE_QUOTA_SIG = get_selector("increase_opcode_quota(uint64,uint64)void")


@dataclass
class GasStation:
    app_id: int
    app_address: str = field(init=False)

    def __post_init__(self):
        self.app_address = algosdk.logic.get_application_address(self.app_id)

    def build_fund_tx(
        self, sender: str, amount: int, suggested_params: transaction.SuggestedParams
    ) -> transaction.Transaction:
        return transaction.PaymentTxn(
            sender=sender,
            receiver=self.app_address,
            amt=amount,
            sp=suggested_params,
        )

    def build_increase_opcode_quota_tx(
        self,
        sender: str,
        count: int,
        suggested_params: transaction.SuggestedParams,
        extra_fee=0,
    ) -> transaction.Transaction:
        return transaction.ApplicationNoOpTxn(
            sender=sender,
            index=self.app_id,
            app_args=[INCREASE_OPCODE_QUOTA_SIG, count, 0],
            sp=sp_fee(suggested_params, (count + 1) * 1000 + extra_fee),
        )


_gas_station: Optional[GasStation] = None


def set_gas_station(app_id: int):
    global _gas_station
    _gas_station = GasStation(app_id)


def get_gas_station() -> GasStation:
    assert _gas_station, "Gas station not set. Use set_gas_station."
    return _gas_station
