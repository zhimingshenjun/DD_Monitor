# -*- coding: utf-8 -*-
"""
通过QThread + websocket获取直播弹幕并返回给播放窗口模块做展示
"""
import asyncio
import zlib
import json
import requests
# from aiowebsocket.converses import AioWebSocket
from PyQt5.QtCore import QThread, pyqtSignal
import logging
from bilibili_api import live


class Live(live.LiveDanmaku):

    def __init__(self, room_display_id):
        super().__init__(room_display_id)

    def register(self, event: str, func: callable):
        self.__getattribute__("_LiveDanmaku__event_handlers")[event].append(func)


class remoteThread(QThread):
    message = pyqtSignal(str)

    def __init__(self, roomID):
        super(remoteThread, self).__init__()
        self.roomID = roomID
        if len(self.roomID) <= 3:
            if self.roomID == '0':
                return
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'}
            html = requests.get('https://live.bilibili.com/' +
                                self.roomID, headers=headers).text
            for line in html.split('\n'):
                if '"roomid":' in line:
                    self.roomID = line.split('"roomid":')[1].split(',')[0]

    async def startup(self):
        self.roomID = int(self.roomID)
        self.room = Live(self.roomID)
        self.room.add_event_listener('DANMU_MSG', self.danmu)  # 用户发送弹幕
        # self.room.add_event_listener('SEND_GIFT', self.gift)  # 礼物
        # self.room.add_event_listener('COMBO_SEND', self.combo_gift)  # 礼物连击
        # self.room.add_event_listener('GUARD_BUY', self.guard)  # 续费大航海
        self.room.add_event_listener('SUPER_CHAT_MESSAGE', self.sc)  # 醒目留言（SC）
        # self.room.add_event_listener('INTERACT_WORD', self.enter)  # 用户进入直播间
        await self.room.connect()
        # await asyncio.wait([self.room.connect()])

    async def danmu(self, jd):
        self.message.emit(jd['data']['info'][1])

    async def gift(self, event):
        print(event)

    async def combo_gift(self, event):
        print(event)

    async def guard(self, event):
        print(event)

    async def sc(self, jd):
        jd = jd['data']
        self.message.emit(
            f"【SC(￥{jd['data']['price']}) {jd['data']['user_info']['uname']}: {jd['data']['message']}】"
        )

    async def enter(self, event):
        print(event)

    def printDM(self, data):
        packetLen = int(data[:4].hex(), 16)
        ver = int(data[6:8].hex(), 16)
        op = int(data[8:12].hex(), 16)

        if len(data) > packetLen:
            self.printDM(data[packetLen:])
            data = data[:packetLen]

        if ver == 2:
            data = zlib.decompress(data[16:])
            self.printDM(data)
            return

        if ver == 1:
            if op == 3:
                # print('[RENQI]  {}'.format(int(data[16:].hex(),16)))
                pass
            return

        captainName = {
            0: "",
            1: "总督",
            2: "提督",
            3: "舰长"
        }

        userType = {
            "#FF7C28": "+++",
            "#E17AFF": "++",
            "#00D1F1": "+",
            "": ""
        }

        adminType = ["", "*"]

        def getMetal(jd):
            try:
                medal = []
                if jd['cmd'] == 'DANMU_MSG':
                    jz = captainName[jd['info'][3][10]]
                    if jz:
                        medal.append(jz)
                    medal.append(jd['info'][3][1])
                    medal.append(str(jd['info'][3][0]))
                else:
                    jz = captainName[jd['data']['medal_info']['guard_level']]
                    if jz:
                        medal.append(jz)
                    medal.append(jd['data']['medal_info']['medal_name'])
                    medal.append(str(jd['data']['medal_info']['medal_level']))
                return "|" + "|".join(medal) + "|"
            except:
                return ""

        if op == 5:
            try:
                jd = json.loads(data[16:].decode('utf-8', errors='ignore'))
                if jd['cmd'] == 'DANMU_MSG':
                    self.message.emit(
                        # f"{userType[jd['info'][2][7]]}{adminType[jd['info'][2][2]]}{getMetal(jd)} {jd['info'][2][1]}: {jd['info'][1]}"
                        f"{jd['info'][1]}"
                    )
                elif jd['cmd'] == 'SUPER_CHAT_MESSAGE':
                    self.message.emit(
                        f"【SC(￥{jd['data']['price']}) {getMetal(jd)} {jd['data']['user_info']['uname']}: {jd['data']['message']}】"
                    )
                elif jd['cmd'] == 'SEND_GIFT':
                    if jd['data']['coin_type'] == "gold":
                        self.message.emit(
                            f"** {jd['data']['uname']} {jd['data']['action']}了 {jd['data']['num']} 个 {jd['data']['giftName']}"
                        )
                elif jd['cmd'] == 'USER_TOAST_MSG':
                    self.message.emit(
                        f"** {jd['data']['username']} 上了 {jd['data']['num']} 个 {captainName[jd['data']['guard_level']]}"
                    )
                elif jd['cmd'] == 'ROOM_BLOCK_MSG':
                    self.message.emit(
                        f"** 用户 {jd['data']['uname']} 已被管理员禁言"
                    )
                elif jd['cmd'] == 'INTERACT_WORD':
                    self.message.emit(
                        f"## 用户 {jd['data']['uname']} 进入直播间"
                    )
                elif jd['cmd'] == 'ENTRY_EFFECT':
                    self.message.emit(
                        f"## {jd['data']['copy_writing_v2']}"
                    )
                elif jd['cmd'] == 'COMBO_SEND':
                    self.message.emit(
                        f"** {jd['data']['uname']} 共{jd['data']['action']}了 {jd['data']['combo_num']} 个 {jd['data']['gift_name']}"
                    )
            except:
                logging.exception('弹幕输出失败')

    def setRoomID(self, roomID):
        self.roomID = int(roomID)

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self.startup())
