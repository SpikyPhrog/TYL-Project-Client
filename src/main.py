import flet as ft
from modules.Bulgalingo.MemoryGame.memoryGame import memory_game_view
from modules.MusicPlayer.musicPlayer import music_player_view
from Utils.Clock import Clock


async def main(page : ft.Page):
    page.title = "The Land Yard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 50
    appbar_text_ref = ft.Ref[ft.Text]()
    clock = Clock()
    appbar = ft.AppBar(title=ft.Text("Main page", ref=appbar_text_ref),
            actions=[clock],
            center_title=True,
            bgcolor=ft.Colors.GREEN,
        )

    async def start_memory_game():
        appbar_text_ref.current.value = "Memory Game"
        await page.push_route("/memory_game")

    async def start_music_player():
        appbar_text_ref.current.value = "Radio"
        await page.push_route("/music_player")

    async def route_change():
        print(f"Route change {page.route}")
        page.views.clear()
        page.views.append(
            ft.View(
                route="/",
                appbar = appbar,
                controls = [
                    ft.SafeArea(
                        expand=True,
                        content=ft.GridView(
                            expand=True,
                            runs_count=5,
                            max_extent=250,
                            child_aspect_ratio=1.0,
                            spacing=5,
                            run_spacing=5,
                            controls=[
                                ft.Button("Memory Game", on_click = start_memory_game),
                                ft.Button("Music Player", on_click = start_music_player)
                            ]
                        )
                    )
                ]
            )
        )

        if page.route == "/memory_game":
            page.views.append(
                ft.View(route="/memory_game",
                        appbar = appbar,
                        controls = memory_game_view())
            )
        if page.route == "/music_player":
            page.views.append(
                ft.View(route="/music_player",
                        appbar = appbar,
                        controls = await music_player_view(page)
                        )
            )

        page.update()

    async def view_pop(e):
        if e.view is not None:
            print(f"View pop {e.view}")
            page.views.remove(e.view)
            top_view = page.views[-1]
            await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    await route_change()

ft.run(main)