import flet as ft
import asyncio
import datetime

class Clock(ft.Text):
    def __init__(self):
        super().__init__(value="--:--", size=27)
        self.running = False
        self._task = None

    def did_mount(self):
        self.running = True
        self._task = self.page.run_task(self.ClockTick)

    def will_unmount(self):
        self.running = False
        self._task.cancel()

    async def ClockTick(self):
        while self.running:
            self.value = datetime.datetime.now().strftime("%H:%M")
            self.update()
            await asyncio.sleep(1)
