
# app/__main__.py


def main() -> None:

    from app.helpers.cli import parse_args

    args = parse_args()

    if args.platform == "telegram":
        from src.main.telegram import main as run
    if args.platform == "teams":
        from src.main.teams import main as run

    run()


if __name__ == "__main__":
    main()
