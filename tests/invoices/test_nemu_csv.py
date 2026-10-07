import csv
import io
from dataclasses import replace
from decimal import Decimal

import pytest

from ksef_mcp.invoices.statement import StatementRow, rendered
from tests.support.synthetic import synthetic_metadata


@pytest.mark.parametrize(
    "text", ["=1+1", "+1+1", "-1+1", "@SUM(1)", "  =1", "\tplain", "\rplain", "\nplain"]
)
def test_csv_treats_counterparty_text_as_text_without_changing_signed_amounts(text: str) -> None:
    invoice = replace(
        synthetic_metadata(1),
        seller_invoice_number=text,
        seller_name=text,
        gross_amount=Decimal("-12.30"),
    )
    output = rendered((StatementRow(invoice=invoice, code=None),))
    row = list(csv.reader(io.StringIO(output), delimiter=";"))[1]
    assert row[1] == "'" + text
    assert row[4] == "'" + text
    assert row[5] == "-12,30"
