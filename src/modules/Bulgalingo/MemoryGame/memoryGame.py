import flet as ft
import random
import urllib.request
import json
import asyncio
import os
from dotenv import load_dotenv
from dataclasses import dataclass

DIFFICULTY_EASY = 10
DIFFICULTY_MEDIUM = 20
DIFFICULTY_HARD = 40

load_dotenv()

@dataclass
class Challenge:
    bg_name : str
    en_name : str
    emoji : str

class Card(ft.Container):
    game_manager = None

    def __init__(self, challenge : str, emoji : str = ""):
        self.challenge = challenge
        self.emoji = emoji
        self.challenge_resolved = False
        self.color_clicked = "#c6ddb3"
        self.color_hovered = "#9bf6ff"
        self.color_normal = "#ffbdd4"
        super().__init__(
            bgcolor = self.color_normal,
            ink = True,
            expand = True,
            border_radius = 10,
            on_click = self.OnClicked,
            alignment = ft.Alignment(0,0)
        )

    def ResetOnClicked(self):
        self.bgcolor = self.color_normal
        self.content = None
        self.update()

    async def OnClicked(self):
        await Card.game_manager.CheckCardMatching(self)


class GameManager:
    def __init__(self):
        self.difficulty = DIFFICULTY_EASY # DEFAULT
        self.challenges = [] # [CHALLENGE] all challenges
        self.clicked_card = [] # [CARD] the pair to match
        self.deck = [] # [CARD] dealt deck
        self.score = 0
        self.resolved_pairs = 0 # if this is half of the difficulty then the level is complete
        self.on_level_complete = None
        Card.game_manager = self

    def Restart(self):
        self.deck.clear()
        self.clicked_card.clear()
        self.resolved_pairs = 0
        self.difficulty = 0
        self.SetupDeck()

    def LoadData(self):
        print("Loading data...")
        link = os.getenv("ChallengesURL")

        if link is not None:
            request = urllib.request.Request(
                link,
                headers={
                        "User-Agent" : "Mozilla/5.0"
                        })

            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode("utf-8"))

        return data

    def InitCards(self):
        challenge_data = self.LoadData()

        for challenge in challenge_data:
            self.challenges.append(Challenge(challenge['bulgarian_name'], challenge['english_name'], challenge['emoji']))


    async def ScoreCard(self):
        self.score += 1
        await asyncio.sleep(1.2)

        for card in self.clicked_card:
            card.visible = False
            card.challenge_resolved = True
            card.update()

        self.resolved_pairs += 1
        self.clicked_card.clear()
        self.CheckResovledPairs()

    async def CheckCardMatching(self, card : Card):

        if len(self.clicked_card) >= 2:
            return

        # No clicking on the same card twice!
        if card in self.clicked_card:
            return

        card.bgcolor = card.color_clicked
        card.content = ft.Text(f"{card.challenge} {card.emoji}", size = 25, color = ft.Colors.BLACK)
        card.update()

        self.clicked_card.append(card)

        if len(self.clicked_card) < 2:
            return

        cardA = self.clicked_card[0].challenge
        cardB = self.clicked_card[1].challenge

        for challenge in self.challenges:
            if challenge.bg_name == cardA:
                if challenge.en_name == cardB:
                    await self.ScoreCard()
                else:
                    await self.FlipCards()

            if challenge.en_name == cardA:
                if challenge.bg_name == cardB:
                    await self.ScoreCard()
                else:
                    await self.FlipCards()

    def SetDifficulty(self, difficulty : int):
        self.difficulty = difficulty

    async def FlipCards(self):
        await asyncio.sleep(1)

        for card in self.clicked_card:
            card.ResetOnClicked()
        self.clicked_card.clear()

    def GetChallenges(self, amount):
        random.shuffle(self.challenges)
        listOfChallenges = []
        for i in range(0, amount):
            listOfChallenges.append(self.challenges[i])

        return listOfChallenges

    def SetupDeck(self):
        i = 0
        swapLanguages = False
        challenges = self.GetChallenges(self.difficulty)

        for j in range (0, self.difficulty):
            if j == self.difficulty / 2:
                swapLanguages = True

            if swapLanguages:
                self.deck.append(Card(challenges[i].bg_name, challenges[i].emoji))
                i += 1
            else:
                self.deck.append(Card(challenges[j].en_name))

        random.shuffle(self.deck)

    def StartGame(self):
        self.score = 0
        self.SetupDeck()

    def CheckResovledPairs(self):
        if self.resolved_pairs == self.difficulty / 2:
            if self.on_level_complete:
                self.on_level_complete()

class UIManager:
    def __init__(self, gameManager : GameManager):
        self.game_manager = gameManager
        self.content = ft.Container()
        self.game_manager.on_level_complete = self.Screen_Complete

    def Menu_DifficultySelect(self):
        self.content.content =  ft.Column(
            expand = True,
            controls = [
                ft.Button("Easy", on_click= lambda: self.Button_SelectDifficulty(DIFFICULTY_EASY)),
                ft.Button("Medium", on_click=lambda :self.Button_SelectDifficulty(DIFFICULTY_MEDIUM)),
                ft.Button("Hard", on_click=lambda : self.Button_SelectDifficulty(DIFFICULTY_HARD))
            ]
        )

    def Menu_Loading(self):
        self.content.content = ft.Column(
            expand = True,
            controls = [
                ft.Text("LOADING ... "),
                ft.ProgressBar(width = 400)
            ]
        )
        self.game_manager.InitCards()
        self.Menu_DifficultySelect()

    def Button_SelectDifficulty(self, difficulty : int):
        self.game_manager.SetDifficulty(difficulty)
        print(difficulty)
        self.GameView()

    def Screen_Complete(self):
        self.content.content = (
            ft.Column(
                expand = True,
                controls = [
                    ft.Text(f"Level complete, score: {self.game_manager.score}"),
                    ft.Button("Restart", on_click=self.Button_Restart)
                ]
            )
        )
        self.content.update()

    def Button_Restart(self, e):
        self.Menu_DifficultySelect()
        self.game_manager.Restart()
        self.content.update()


    def GameView(self):
        self.game_manager.StartGame()
        self.content.content = ft.GridView(
            expand = True,
            runs_count = 5,
            max_extent = 150,
            child_aspect_ratio = 1.0,
            spacing = 5,
            run_spacing = 5,
            controls = [
                self.game_manager.deck[i]
                for i in range(0, len(self.game_manager.deck))
            ]
        )


def memory_game_view():
    game_manager = GameManager()
    ui_manager = UIManager(game_manager)
    ui_manager.Menu_Loading()

    return ft.SafeArea(
        expand = True,
        content = ui_manager.content
    )
