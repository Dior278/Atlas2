"""Atlas in the Aparté package: one engine, one API, one interface."""

import argparse

from .workspace.api.app import create_app

app = create_app()


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Atlas, coéquipier de réunion local")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Adresse d’écoute ; le contrôle de l’application reste réservé au client local",
    )
    parser.add_argument("--ssl-certfile", default=None)
    parser.add_argument("--ssl-keyfile", default=None)
    args = parser.parse_args()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        ws_max_size=131072,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile,
    )


if __name__ == "__main__":
    main()
