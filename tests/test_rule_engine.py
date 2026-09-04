from datetime import datetime
import pytest
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.transaction import Transaction, TransactionDataset
from src.rules.engine import evaluate_all_rules


def test_rule_engine_runs_all_four_rules():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt, description="D", payee="P1", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=dt, description="D", payee="P1", amount=200.0, channel="UPI")

    ds = TransactionDataset(transactions=[t1, t2])
    eval_res = evaluate_all_rules(ds)

    assert eval_res.customer_id == "C1"
    assert eval_res.evaluated_at_transaction_count == 2
    assert len(eval_res.rules) == 4
    rule_ids = [r.rule_id for r in eval_res.rules]
    assert rule_ids == ["R01", "R02", "R03", "R04"]
    # Non-triggered rules are visible
    for r in eval_res.rules:
        assert isinstance(r.triggered, bool)


def test_single_transaction_triggers_multiple_rules():
    # Baseline transactions
    t_base1 = Transaction(transaction_id="TB1", customer_id="C1", timestamp=datetime(2026, 1, 1, 10, 0), description="D", payee="P1", amount=100.0, channel="UPI")
    t_base2 = Transaction(transaction_id="TB2", customer_id="C1", timestamp=datetime(2026, 1, 2, 10, 0), description="D", payee="P1", amount=200.0, channel="UPI")

    # Target transaction: ₹250,000 at 01:45 AM (odd hours)
    t_multi = Transaction(transaction_id="TXN_MULTI", customer_id="C1", timestamp=datetime(2026, 1, 15, 1, 45), description="D", payee="P2", amount=250000.0, channel="UPI")

    ds = TransactionDataset(transactions=[t_base1, t_base2, t_multi])
    baseline = build_customer_baseline(TransactionDataset(transactions=[t_base1, t_base2]))

    eval_res = evaluate_all_rules(ds, baseline)
    r_map = {r.rule_id: r for r in eval_res.rules}

    # R01 (large amount) & R03 (odd hours) should both trigger independently
    assert r_map["R01"].triggered is True
    assert "TXN_MULTI" in r_map["R01"].transaction_ids

    assert r_map["R03"].triggered is True
    assert "TXN_MULTI" in r_map["R03"].transaction_ids


def test_rule_engine_empty_dataset():
    eval_res = evaluate_all_rules(None)
    assert eval_res.evaluated_at_transaction_count == 0
    assert eval_res.rules == []
