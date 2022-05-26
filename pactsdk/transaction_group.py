import base64

from algosdk.future import transaction

from pactsdk.exceptions import PactSdkError


class TransactionGroup:
    """A convenience class to make managing Algorand transactions groups easier."""

    transactions: list[transaction.Transaction]
    """A list of transactions in a group."""

    def __init__(self, transactions: list[transaction.Transaction]):
        """Creates the TransactionGroup from an array of transactions by assigning a group id to each transaction.

        Args:
            transactions: A list of transactions to put in a group.

        Raises:
            PactSdkError: If the list is empty (length 0) or if the group id was not assigned to the transactions due to e.g. a failure in the algorand sdk.
        """
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
        """Signs all the transactions in the group with the secrete key.

        Using the private_key passed in assigns all the transactions stored internally for the transaction group.

        Args:
            private_key: Sign the transactions with this private key.

        Returns:
            A list of encoded signed transactions as per the Transaction.sign from the Algorand sdk.
        """
        return [tx.sign(private_key) for tx in self.transactions]

    @property
    def group_id(self):
        """
        Returns
            The group id as a base64 encoded string.
        """
        return base64.b64encode(self.group_id_buffer)
