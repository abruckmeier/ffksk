import rules


@rules.predicate
def perm_is_financial_admin_and_transaction_is_paypal(user, transaction=None):
    """
    Predicate to check if the user is a financial admin and the transaction is a PayPal transaction. If both is given,
    access is granted.

    :param user: KioskUser object
    :param transaction: GeldTransaktionen object
    :return: True or False
    """
    if not transaction:
        return False
    else:
        return (user.has_perm('profil.do_verwaltung_financial_operations')
                and getattr(transaction, 'assigned_geld_transaktion', None) is not None)
