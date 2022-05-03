"""Utility class for managing a list of Transactions as a Transaction Group.

A single class to manage the operations on a list of Transactions as a Transaction Group. The
    class sets the transaction group id on the transactions and has functions to sign the transaction group as a whole.

    Arguments:
        None

"""
from algosdk.future import transaction


class TransactionGroup:
    """TransactionGroup represents a group of transactions that are to be treated together.

    The class is used to set the list of transaction as a group and then has a convenience function to act on the
    transaction group.

    Attributes:
        tranactions: A list of transactions assigned to a group.
    """

    def __init__(self, transactions: list[transaction.Transaction]):
        """Groups the transactions and initializes the class.

        Assigns the group property to the transactions passed in and sets it to the attribute.

        Args:
            transactions (list[ `algosdk.future.transaction.Transaction` ]): A set of transactions to manage as a group.
        """
        self.transactions = transaction.assign_group_id(transactions)

    def sign(self, private_key: str) -> list[str]:
        """Signs all the transactions with the private key.

        Using the private_key passed in assigns all the transactions stored internally for the transaction group.

        Args:
            private_key (str): The private signing key of an account

        Returns:
            list[`algosdk.future.transaction.SignedTransaction`]: List of the transactions signed with the primary key.
        """
        return [tx.sign(private_key) for tx in self.transactions]
