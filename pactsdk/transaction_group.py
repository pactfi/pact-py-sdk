import base64

from algosdk.future import transaction

from pactsdk.exceptions import PactSdkError


class TransactionGroup:
    def __init__(self, transactions: list[transaction.Transaction]):
        if len(transactions) == 0:
            raise PactSdkError(
                "Cannot create TransactionGroup: empty transactions list."
            )
        self.transactions = transaction.assign_group_id(transactions)

        first_tx = self.transactions[0]
        if not first_tx.group:
            raise PactSdkError("Cannot retrieve group id from transaction.")
        self.group_id_buffer = first_tx.group

    def sign(self, private_key: str) -> list[str]:
        return [tx.sign(private_key) for tx in self.transactions]

    @property
    def group_id(self):
        return base64.b64encode(self.group_id_buffer)
