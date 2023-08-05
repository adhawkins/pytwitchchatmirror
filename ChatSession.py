from twitchAPI.twitch import Twitch, TwitchUserFollow
from twitchAPI.helper import first
from twitchAPI.types import AuthScope
from twitchAPI.chat import Chat, ChatEvent

from pprint import pprint


class ChatSession:
    SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.USER_READ_FOLLOWS]

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
        self.mirrorEnabled = False

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

        self.chat.register_command("mirror", self.onMirrorCommand)

        self.chat.start()

    async def shutdown(self):
        self.chat.stop()
        await self.twitch.close()

    async def onReady(self, readyEvent):
        for channel in self.channels:
            channelUser = await first(self.twitch.get_users(logins=f"{channel}"))
            followedChannels = await self.twitch.get_followed_channels(
                self.userID, broadcaster_id=channelUser.id
            )

            if not followedChannels.data:
                print(f"User {self.userName} ({self.userID}) does not follow {channel}")

        await self.chat.join_room(self.channels)

    async def onMessage(self, messageEvent):
        if self.mirrorEnabled and not messageEvent.text.startswith("!"):
            if messageEvent.user.name != self.userName:
                for channel in self.channels:
                    if channel != messageEvent.room.name:
                        await self.chat.send_message(
                            channel,
                            f"[{messageEvent.room.name}]{messageEvent.user.name}: {messageEvent.text}",
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

    async def onMirrorCommand(self, commandArgs):
        # print(
        #     f"User '{commandArgs.user.name}' in '{commandArgs.room.name}' sent command '{commandArgs.name}' - args: '{commandArgs.parameter}'"
        # )

        validArgs = False
        parameter = commandArgs.parameter
        enable = False
        emptyArgs = False

        if commandArgs.user.mod or commandArgs.user.name == commandArgs.room.name:
            if parameter == "":
                emptyArgs = True
                validArgs = True
            elif parameter in ["1", "on", "true"]:
                validArgs = True
                enable = True
            elif parameter in ["0", "off", "false"]:
                validArgs = True
                enable = False

            if validArgs:
                if emptyArgs:
                    await commandArgs.reply(
                        f"Chat mirroring is currently {'enabled' if self.mirrorEnabled else 'disabled'}"
                    )
                else:
                    self.mirrorEnabled = enable
                    await commandArgs.reply(
                        f"Chat mirroring is now {'enabled' if self.mirrorEnabled else 'disabled'}"
                    )
            else:
                await commandArgs.reply(
                    f"Usage: {commandArgs.name}' 0 | off | false | 1 | on | true"
                )
        else:
            print(
                f"User '{commandArgs.user.name}' is not a moderator in {commandArgs.room.name} ({commandArgs.user.user_type})"
            )
