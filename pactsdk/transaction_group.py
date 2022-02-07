from algosdk.future import transaction


class TransactionGroup:
    def __init__(self, transactions: list[transaction.Transaction]):
        self.transactions = transaction.assign_group_id(transactions)

    def sign(self, private_key: str) -> list[str]:
        return [tx.sign(private_key) for tx in self.transactions]
