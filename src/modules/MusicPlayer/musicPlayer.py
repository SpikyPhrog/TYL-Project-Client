import flet as ft
import flet_audio as fta
import websockets
import json
import os
from dotenv import load_dotenv

from Utils.Clock import Clock

load_dotenv()

class RadioWebSocket:
    def __init__(self, url):
        self.url = url
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.url)

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()

    async def send(self, message):
        if self.websocket is None:
            await self.connect()
        await self.websocket.send(json.dumps(message))

    async def receive(self):
        if self.websocket is None:
            await self.connect()

        message = await self.websocket.recv()
        return json.loads(message)

class CurrentlyPlayingDisplay(ft.Text):
    def __init__(self, radio : RadioWebSocket):
        super().__init__(value="Currently Playing:", size=30)
        self.running = False
        self._task = None
        self.radio = radio

    def did_mount(self):
        self.running = True
        self._task = self.page.run_task(self.UpdateSong)

    def will_unmount(self):
        self.running = False

        if self._task:
            self._task.cancel()
            self._task = None

    async def UpdateSong(self):
      while self.running:
            try:
                message = await self.radio.receive()

                print(f"Message received: {message}")
                if message.get("type") != "now_playing":
                    continue

                track = message.get("data", {})

                artist = track.get("artist")
                title = track.get("title")

                if artist and title:
                    self.value = f"{artist} - {title}"

                elif title:
                    self.value = title

                else:
                    self.value = "Currently Playing: Unknown"

                self.update()

            except Exception as e:
                print(f"Websocket error : {e}")
                break

# class Playlist(ft.Column):
#     def __init__(self, radio : LSRadio):
#         self.radio = radio

class MPlayer(ft.BottomAppBar):
    def __init__(self, page : ft.Page):
        self.clock = Clock()
        self.radio = RadioWebSocket(os.getenv("Websocket"))
        self.currentlyPlaying = CurrentlyPlayingDisplay(self.radio)

        self.playerControls = ft.Row(
            controls = [
                ft.IconButton(ft.CupertinoIcons.FORWARD_FILL, on_click = self.skipSong),
            ]
        )
        self.playerDisplay = ft.Row(
            controls = [
                self.currentlyPlaying
            ]
        )
        # self.playlist = ft.Column(
        #     controls = [
        #         ft.Card(
        #             content=ft.ListTile(
        #                 title=ft.Text("Clickable tile"),
        #                 subtitle=ft.Text("Click me"),
        #                 on_click=self.onClick
        #             )
        #         )
        #         for i in range(0, 10)
        #     ]
        # )
        super().__init__(
            content =
                ft.Column(
                    expand = True,
                    controls = [
                        self.playerDisplay,
                        self.playerControls,
                        # self.playlist,
                    ]
                )
        )
    #
    # def onClick(self, e):
    #     self.page.show_snack_bar(ft.SnackBar(ft.Text("TileClicked")))
    #     self.page.update()

    async def skipSong(self, e):
        await self.radio.send({
            "action" : "skip"
        })

    async def getCurrentlyPlaying(self):
        await self.currentlyPlaying.UpdateSong()

    async def OnBeginPlay(self):
        await self.radio.connect()
        await self.radio.send({
            "action" : "get_currently_playing"
        })

async def music_player_view(page : ft.Page):
    player = MPlayer(page)
    await player.OnBeginPlay()

    return ft.SafeArea(
        expand = True,
        content = player
    )