from telebot import types

class Chat_storage:
    __slots__ = ("id2data")
    def __init__(self) -> None:
        self.id2data = {}
    
    def chat(self, chatid:str):
        chatid = str(chatid)
        if not chatid in self.id2data:
            self.id2data[chatid] = {}

        return self.id2data[chatid]
    
    def msg(self, msg: types.Message):
        chat = str(msg.chat.id)
        if not chat in self.id2data:
            self.id2data[chat] = {}

        return self.id2data[chat]
    
    def resetmsg(self, msg: types.Message):
        chat = str(msg.chat.id)
        self.id2data[chat] = {}