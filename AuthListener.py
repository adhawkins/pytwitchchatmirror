from aiohttp import web
import asyncio
import requests
import json
from twitchAPI.oauth import validate_token

from pprint import pprint


class AuthListener:
    def __init__(self, clientID, clientSecret, reauthCallback):
        self.clientID = clientID
        self.clientSecret = clientSecret
        self.reauthCallback = reauthCallback

    async def initialise(self):
        self.app = web.Application()
        self.app.add_routes([web.get("/auth", self.authHandler)])
        self.app.add_routes([web.get("/create", self.createHandler)])

        self.runner = web.AppRunner(self.app, access_log=None)
        await self.runner.setup()
        site = web.TCPSite(self.runner, port=8100)
        await site.start()

    async def shutdown(self):
        await self.runner.cleanup()

    async def createHandler(self, request):
        response = (
            "<h1>ADH Chat Mirror login</h1>"
            "<p>"
            "To authorise your bot to read and post chat, visit the following link: "
            f'<a href="https://id.twitch.tv/oauth2/authorize?client_id={self.clientID}&redirect_uri=https://twitch-chat.gently.org.uk/auth&response_type=code&state=xyz123&scope=chat%3Aedit%20chat%3Aread%20user%3Aread%3Afollows">Click here</a>'
            "<p>"
        )

        return web.Response(text=response, content_type="text/html")

    async def authHandler(self, request):
        payload = {
            "client_id": self.clientID,
            "client_secret": self.clientSecret,
            "code": request.query["code"],
            "grant_type": "authorization_code",
            "redirect_uri": "https://twitch-chat.gently.org.uk/auth",
        }

        r = requests.post("https://id.twitch.tv/oauth2/token", data=payload)
        tokens = r.json()

        if "status" in tokens and tokens["status"] == 400:
            return web.Response(text=f"Invalid request\n")
        else:
            validate = await validate_token(tokens["access_token"])

            if self.reauthCallback:
                apiKey = await self.reauthCallback(
                    validate["user_id"],
                    validate["login"],
                    tokens["access_token"],
                    tokens["refresh_token"],
                )

                response = (
                    "<p>Thank you for registering.<p>"
                    # f"<p>Your API key is '<b>{apiKey}</b>', please make a note of it.</p>"
                )

                return web.Response(text=response, content_type="text/html")
            else:
                return web.Response(text=f"Internal error - no auth listener'\n")
