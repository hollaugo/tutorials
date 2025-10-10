import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


class _FakeSmithery:
    def server(self, *args, **kwargs):  # pragma: no cover - shim logic is trivial
        def decorator(fn):
            return fn

        return decorator


def _ensure_smithery_stub():
    """Provide a lightweight smithery decorator stub for local tests."""

    if "smithery.decorators" in sys.modules:
        return

    fake_module = types.ModuleType("smithery.decorators")
    fake_module.smithery = _FakeSmithery()
    sys.modules.setdefault("smithery", types.ModuleType("smithery"))
    sys.modules["smithery.decorators"] = fake_module


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_ensure_smithery_stub()

PACKAGE_NAME = "financial_server"
MODULE_NAME = f"{PACKAGE_NAME}.server"
MODULE_PATH = PROJECT_ROOT / "financial_server" / "server.py"

package_module = types.ModuleType(PACKAGE_NAME)
package_module.__path__ = [str(PROJECT_ROOT / "financial_server")]
sys.modules.setdefault(PACKAGE_NAME, package_module)

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
server_module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = server_module
spec.loader.exec_module(server_module)
setattr(package_module, "server", server_module)

ConfigSchema = server_module.ConfigSchema
create_server = server_module.create_server


class FakeTicker:
    """Deterministic ticker fixture for unit tests."""

    def __init__(self, ticker: str):
        base_index = pd.Index([pd.Timestamp("2024-01-05")])
        self._history = pd.DataFrame(
            {
                "Close": [150.0],
                "Volume": [1_000_000],
            },
            index=base_index,
        )

        self._sec_filings = pd.DataFrame(
            {
                "Type": ["10-K"],
                "Date": [pd.Timestamp("2023-12-31")],
            },
            index=pd.Index(["abc123"], name="filingId"),
        )

        self.analyst_price_targets = {
            "targetHigh": float("nan"),
            "targetLow": 120.5,
        }

        self.recommendations = pd.DataFrame(
            {
                "To Grade": ["Strong Buy"],
                "Date": [pd.Timestamp("2023-11-01")],
            },
            index=pd.Index([0], name="row"),
        )

        self.dividends = pd.Series(
            [0.5],
            index=pd.Index([pd.Timestamp("2023-12-01")]),
            name="Dividends",
        )

        self.splits = pd.Series(
            [2.0],
            index=pd.Index([pd.Timestamp("2022-08-31")]),
            name="Splits",
        )

        self.institutional_holders = pd.DataFrame(
            {
                "Holder": ["Big Fund"],
                "% Out": [0.05],
            },
            index=pd.Index([0], name="row"),
        )

        self.insider_transactions = pd.DataFrame(
            {
                "Insider": ["Jane Doe"],
                "Shares": [1000],
            },
            index=pd.Index([0], name="row"),
        )

        statement_index = pd.Index(["Total Assets"], name="Account")
        self.balance_sheet = pd.DataFrame(
            {pd.Timestamp("2023-12-31"): [1_000_000]},
            index=statement_index,
        )
        self.income_stmt = pd.DataFrame(
            {pd.Timestamp("2023-12-31"): [250_000]},
            index=pd.Index(["Net Income"], name="Account"),
        )
        self.cashflow = pd.DataFrame(
            {pd.Timestamp("2023-12-31"): [150_000]},
            index=pd.Index(["Operating Cash Flow"], name="Account"),
        )

        self.info = {
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }

    # yfinance API methods -------------------------------------------------
    def history(self, period: str = "5d") -> pd.DataFrame:
        return self._history.copy()

    def get_sec_filings(self):
        return self._sec_filings.copy()


@pytest.fixture(name="server")
def fixture_server(monkeypatch):
    monkeypatch.setattr("yfinance.Ticker", lambda ticker: FakeTicker(ticker))
    return create_server()


@pytest.fixture(name="ctx")
def fixture_ctx():
    return SimpleNamespace(session_config=ConfigSchema())


def _call_tool(server, name: str, *args):
    tool = server._tool_manager.get_tool(name)
    return tool.fn(*args)


def test_get_stock_summary_returns_expected_text(server, ctx):
    result = _call_tool(server, "get_stock_summary", "AAPL", ctx)
    assert "AAPL Summary" in result
    assert "Close Price: $150.00" in result
    assert "Volume: 1000000" in result


def test_get_stock_summary_handles_empty_ticker(server, ctx):
    result = _call_tool(server, "get_stock_summary", "   ", ctx)
    assert result == "Ticker symbol is required."


def test_get_sec_filings_returns_records(server, ctx):
    filings = _call_tool(server, "get_sec_filings", "AAPL", ctx)
    assert filings[0]["filingId"] == "abc123"
    assert filings[0]["Date"].startswith("2023-12-31")


def test_get_analyst_targets_sanitises_nan(server, ctx):
    targets = _call_tool(server, "get_analyst_targets", "AAPL", ctx)
    assert targets["targetHigh"] is None
    assert targets["targetLow"] == 120.5


def test_get_recommendations_returns_records(server, ctx):
    recs = _call_tool(server, "get_recommendations", "AAPL", ctx)
    assert recs[0]["To Grade"] == "Strong Buy"


def test_get_dividends_returns_date_keys(server, ctx):
    dividends = _call_tool(server, "get_dividends", "AAPL", ctx)
    assert list(dividends.values()) == [0.5]
    assert list(dividends.keys())[0].startswith("2023-12-01")


def test_get_splits_returns_date_keys(server, ctx):
    splits = _call_tool(server, "get_splits", "AAPL", ctx)
    assert list(splits.values()) == [2.0]
    assert list(splits.keys())[0].startswith("2022-08-31")


def test_get_institutional_holders_returns_records(server, ctx):
    holders = _call_tool(server, "get_institutional_holders", "AAPL", ctx)
    assert holders[0]["Holder"] == "Big Fund"


def test_get_insider_transactions_returns_records(server, ctx):
    insiders = _call_tool(server, "get_insider_transactions", "AAPL", ctx)
    assert insiders[0]["Insider"] == "Jane Doe"


def test_get_sector_info_returns_expected_mapping(server, ctx):
    info = _call_tool(server, "get_sector_info", "AAPL", ctx)
    assert info == {"sector": "Technology", "industry": "Consumer Electronics"}


def test_get_financial_statements_returns_nested_dict(server, ctx):
    statements = _call_tool(server, "get_financial_statements", "AAPL", ctx)
    balance_sheet = statements["balance_sheet"]
    key = next(iter(balance_sheet))
    assert key.startswith("2023-12-31")
    assert balance_sheet[key]["Total Assets"] == 1_000_000


def test_summarize_filing_returns_summary(monkeypatch, server, ctx):
    class FakeResponse:
        status_code = 200
        content = b"<html><body><p>This is a sample filing. It contains useful data. Second sentence.</p></body></html>"

    class FakeLoader:
        def __init__(self, path):
            self.path = path

        def load(self):
            return [SimpleNamespace(page_content="Sentence one. Sentence two. Sentence three. Sentence four.")]

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(server_module, "BSHTMLLoader", FakeLoader)

    summary = _call_tool(server, "summarize_filing", "https://sec.gov/xyz", ctx)
    assert summary.startswith("Summary of SEC filing")
    assert "Sentence one" in summary
