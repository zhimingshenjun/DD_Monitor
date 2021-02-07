# -*- coding: utf-8 -*-
"""
通过QThread + websocket获取直播弹幕并返回给播放窗口模块做展示
"""
import asyncio
import zlib
import json
import requests
from aiowebsocket.converses import AioWebSocket
from PyQt5.QtCore import QThread, pyqtSignal
import logging


class remoteThread(QThread):
    """
    TODO: 换用 bilibili_api.live.LiveDanmaku(room_display_id)
    """
    message = pyqtSignal(str)

    def __init__(self, roomID):
        super(remoteThread, self).__init__()
        self.roomID = roomID
        if len(self.roomID) <= 3:
            if self.roomID == '0':
                return
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'}
            html = requests.get('https://live.bilibili.com/' + self.roomID, headers=headers).text
            for line in html.split('\n'):
                if '"roomid":' in line:
                    self.roomID = line.split('"roomid":')[1].split(',')[0]

    async def startup(self, url):
        logging.info('尝试打开 %s 的弹幕Socket' % self.roomID)
        data_raw = '000000{headerLen}0010000100000007000000017b22726f6f6d6964223a{roomid}7d'
        data_raw = data_raw.format(headerLen=hex(27 + len(self.roomID))[2:],
                                   roomid=''.join(map(lambda x: hex(ord(x))[2:], list(self.roomID))))
        async with AioWebSocket(url) as aws:
            try:
                converse = aws.manipulator
                await converse.send(bytes.fromhex(data_raw))
                tasks = [self.receDM(converse), self.sendHeartBeat(converse)]
                await asyncio.wait(tasks)
            except:
                logging.exception('弹幕Socket打开失败')

    async def sendHeartBeat(self, websocket):
        logging.debug("向%s发送心跳包" % self.roomID)
        hb = '00000010001000010000000200000001'
        while True:
            await asyncio.sleep(30)
            await websocket.send(bytes.fromhex(hb))

    async def receDM(self, websocket):
        while True:
            recv_text = await websocket.receive()
            logging.debug("从%s接收到DM" % self.roomID)
            self.printDM(recv_text)

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

        if op == 5:
            try:
                jd = json.loads(data[16:].decode('utf-8', errors='ignore'))
                if jd['cmd'] == 'DANMU_MSG':
                    self.message.emit(jd['info'][1])
                # elif jd['cmd'] == 'SEND_GIFT':
                #     d = jd['data']
                #     self.message.emit('%s投喂了%s个%s' % (d['uname'], d['num'], d['giftName']))
                # elif jd['cmd'] == 'COMBO_SEND':
                #     d = jd['data']
                #     self.message.emit('%s投喂了%s个%s' % (d['uname'], d['batch_combo_num'], d['gift_name']))
                # elif jd['cmd'] == 'GUARD_BUY':
                #     self.message.emit('%s上了舰长' % jd['data']['username'])
            except:
                logging.exception('弹幕输出失败')

    def setRoomID(self, roomID):
        self.roomID = roomID

    def run(self):
        remote = r'wss://broadcastlv.chat.bilibili.com:2245/sub'
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            asyncio.get_event_loop().run_until_complete(self.startup(remote))
        except:
            logging.exception('弹幕主循环出错')
