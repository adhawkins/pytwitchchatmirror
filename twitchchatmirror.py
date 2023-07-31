#!/usr/bin/env python

from AuthListener import AuthListener
from Config import Config
from ChatSession import ChatSession

from pprint import pprint

import asyncio
import signal

import appsecrets


class TwitchApp:
    def __init__(self):
        signal.signal(signal.SIGINT, self.signalHandler)
        self.finished = False
        self.chats = []

        self.authListener = AuthListener(
            appsecrets.TWITCH_CLIENTID,
            appsecrets.TWITCH_CLIENTSECRET,
            self.authReauthCallback,
        )

    def signalHandler(self, sig, frame):
        self.finished = True

    async def waitFinish(self):
        while not self.finished:
            await asyncio.sleep(0.1)

    async def asyncMain(self):
        await self.authListener.initialise()

        config = Config()

        for user in config.config:
            newChat = ChatSession(
                appsecrets.TWITCH_CLIENTID,
                appsecrets.TWITCH_CLIENTSECRET,
                user["userID"],
                user["login"],
                user["accessToken"],
                user["refreshToken"],
                user["channels"],
                self.userAuthRefreshed,
            )

            await newChat.initialise()

            self.chats.append(newChat)

        await self.waitFinish()

        await self.authListener.shutdown()

        for chat in self.chats:
            await chat.shutdown()

    async def authReauthCallback(self, userID, login, accessToken, refreshToken):
        # print(
        #     f"user: '{userID}', login: '{login}', access: '{accessToken}', refresh: '{refreshToken}'"
        # )

        config = Config()
        config.addUser(userID, login, accessToken, refreshToken)

    def userAuthRefreshed(self, userID, accessToken, refreshToken):
        print(
            f"Main: User auth refreshed, user: {userID}, acccess: '{accessToken}', refresh: '{refreshToken}'"
        )

        config = Config()
        config.updateUserTokens(userID, accessToken, refreshToken)


try:
    twitchApp = TwitchApp()
    asyncio.run(twitchApp.asyncMain())
except asyncio.CancelledError:
    pass
