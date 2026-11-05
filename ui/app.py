"""Public desktop application entry point."""

from .controller import GatewayApp

__all__ = ["GatewayApp"]


def main() -> None:
    GatewayApp().run()


if __name__ == "__main__":
    main()
