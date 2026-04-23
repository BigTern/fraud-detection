from __future__ import annotations

import pandas as pd


def build_model_frame(transactions: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    return transactions.merge(accounts, on="account_id", how="left")
