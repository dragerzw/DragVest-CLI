# main.py (web service entrypoint)
from app import create_app
from app.config import Config


app = create_app(Config)


def main() -> None:
    # Start Flask development server
    app.run(debug=bool(getattr(Config, "DEBUG", True)))


if __name__ == "__main__":
    main()
