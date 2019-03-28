from fastapi import FastAPI
from mafia.api.vanilla import MafiaAPI


#
app = FastAPI()
# mafia_api = MafiaAPI.generate(5)
mafia_api = MafiaAPI()
app.include_router(mafia_api)
