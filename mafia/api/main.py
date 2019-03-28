from fastapi import FastAPI
from mafia.api.vanilla import MafiaAPI

import sys
import argparse
import uvicorn


# Defining the app
app = FastAPI()
# mafia_api = MafiaAPI.generate(5)
mafia_api = MafiaAPI()
app.include_router(mafia_api)


def main(args=None):
    """Runs a Vanilla game."""
    if args is None:
        args = sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8000)
    p.add_argument('--log_level', default='info')
    a = p.parse_args(args)

    uvicorn.run(app, host=a.host, port=a.port, log_level=a.log_level)


if __name__ == "__main__":
    main()
