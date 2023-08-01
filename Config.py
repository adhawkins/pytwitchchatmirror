import json
import os.path


class Config:
    FILENAME = "config.json"

    def __init__(self):
        self.config = []

        self.loadConfig()

    def loadConfig(self):
        if os.path.isfile(Config.FILENAME):
            with open(Config.FILENAME) as f:
                self.config = json.load(f)

    def saveConfig(self):
        with open(Config.FILENAME, "w") as f:
            json.dump(self.config, f)

    def findUser(self, userID):
        return next(
            (i for i, item in enumerate(self.config) if item["userID"] == userID), None
        )

    def addUser(self, userID, login, accessToken, refreshToken):
        currentUser = self.findUser(userID)

        if currentUser == None:
            newUser = {
                "userID": userID,
                "login": login,
                "accessToken": accessToken,
                "refreshToken": refreshToken,
                "channels": [],
            }

            self.config.append(newUser)
        else:
            user = self.config[currentUser]

            user["userID"] = userID
            user["login"] = login
            user["accessToken"] = accessToken
            user["refreshToken"] = refreshToken

            self.config[currentUser] = user

        self.saveConfig()

    def updateUserTokens(self, userID, accessToken, refreshToken):
        currentUser = self.findUser(userID)

        if currentUser != None:
            user = self.config[currentUser]
            user["accessToken"] = accessToken
            user["refreshToken"] = refreshToken

            self.config[currentUser] = user

            self.saveConfig()
