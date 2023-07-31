from twitchAPI.twitch import Twitch, TwitchUserFollow
from twitchAPI.types import AuthScope
from twitchAPI.chat import Chat, ChatEvent

from pprint import pprint


class ChatSession:
    SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

    def __init__(
        self,
        appID,
        appSecret,
        userID,
        userName,
        accessToken,
        refreshToken,
        channels,
        refreshCallback,
    ):
        self.appID = appID
        self.appSecret = appSecret
        self.userID = userID
        self.userName = userName
        self.accessToken = accessToken
        self.refreshToken = refreshToken
        self.channels = channels
        self.refreshCallback = refreshCallback

    async def initialise(self):
        self.twitch = await Twitch(self.appID, self.appSecret)
        await self.twitch.set_user_authentication(
            self.accessToken, ChatSession.SCOPE, self.refreshToken
        )

        self.twitch.user_auth_refresh_callback = self.userAuthRefreshed

        self.chat = await Chat(self.twitch)

        self.chat.register_event(ChatEvent.READY, self.onReady)
        self.chat.register_event(ChatEvent.MESSAGE, self.onMessage)
        self.chat.register_event(ChatEvent.JOIN, self.onJoin)
        self.chat.register_event(ChatEvent.USER_LEFT, self.onLeave)

        self.chat.start()

    async def shutdown(self):
        self.chat.stop()
        self.twitch.close()

    async def onReady(self, readyEvent):
        await self.chat.join_room(self.channels)

    async def onMessage(self, messageEvent):
        for channel in self.channels:
            if channel != messageEvent.room.name:
                await self.chat.send_message(
                    channel,
                    f"{messageEvent.user.name} in {messageEvent.room.name}: {messageEvent.text}",
                )

    async def onJoin(self, joinEvent):
        print(f"User: '{joinEvent.user_name}' joined '{joinEvent.room.name}")

    async def onLeave(self, leaveEvent):
        print(f"User: '{leaveEvent.user_name}' joined '{leaveEvent.room_name}")

    async def userAuthRefreshed(self, accessToken, refreshToken):
        print(
            f"Chat: User auth refreshed, access: '{accessToken}', refresh: '{refreshToken}'"
        )

        if self.refreshCallback:
            self.refreshCallback(self.userID, accessToken, refreshToken)

