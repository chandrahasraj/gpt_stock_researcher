from __future__ import annotations

import argparse
from datetime import date

from src.pipelines.stock_pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run daily watchlist pipeline")
    parser.add_argument("--tickers", nargs="+", required=True)
    parser.add_argument("--model-id", default="public:gpt-x")
    parser.add_argument("--as-of-date", default=str(date.today()))
    parser.add_argument("--max-iters", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for ticker in args.tickers:
        result = run_pipeline(
            ticker=ticker,
            as_of_date=date.fromisoformat(args.as_of_date),
            mode="feeder",
            model_id=args.model_id,
            max_iters=args.max_iters,
        )
        print(f"{ticker}: {result['status']} ({result['run_id']})")


if __name__ == "__main__":
    main()
