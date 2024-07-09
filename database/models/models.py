import uuid
import json
import random
from os import getenv
from copy import deepcopy
from pony.orm import (
    Database,
    PrimaryKey,
    Required,
    Optional,
    Optional,
    Set,
    IntArray,
    StrArray,
)
from .enums import CardType, CardColor, Direction
from utils import errors
from fastapi import status

db = Database()
CARDS = json.load(open("static/cards.json"))


class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True)
    name = Required(str, autostrip=True, unique=True)
    hand = Optional(IntArray)
    uno = Required(bool, default=False)
    match = Optional("Match", reverse="players")
    creator = Optional("Match", reverse="creator")


class Match(db.Entity):
    __randomized_cards = None

    match_id = PrimaryKey(int, auto=True)
    name = Required(str, autostrip=True, unique=True)
    creator = Required(Player)
    code = Required(str, default=lambda: str(uuid.uuid4()))
    min_players = Required(int, default=2)
    max_players = Required(int, default=4)
    started = Required(bool, default=False)
    players = Set(Player)
    state = Optional("MatchState", reverse="match")

    @property
    def num_players(self):
        return len(self.players)

    @property
    def shuffle_cards(self):
        # Debe ser llamada una sola vez
        if self.__randomized_cards is not None:
            return
        self.__randomized_cards = deepcopy(CARDS)
        random.shuffle(self.__randomized_cards)

    @property
    def deal_cards(self):
        for player in self.players:
            for _ in range(7):
                player.hand.append(self.__randomized_cards.pop()["id"])

    @property
    def initialize_pot_and_deck(self):
        while self.__randomized_cards[-1]["type"] == CardType.TAKE_FOUR_WILDCARD:
            random.shuffle(self.__randomized_cards)

        pot = [self.__randomized_cards.pop()["id"]]
        deck = [card["id"] for card in self.__randomized_cards]
        return pot, deck

    def start(self):
        if self.min_players > self.num_players or self.max_players < self.num_players:
            errors.throw(status.HTTP_409_CONFLICT, errors.NOT_ENOUGH_PLAYERS)

        # Mezclamos las cartas
        self.shuffle_cards

        # Repartimos las cartas
        self.deal_cards

        # Inicializamos el pot y el deck
        pot, deck = self.initialize_pot_and_deck

        # Damos un orden a los jugadores
        ordered_players = [player.name for player in self.players]
        random.shuffle(ordered_players)
        random.shuffle(ordered_players)

        self.started = True

        state = MatchState(
            match=self, pot=pot, deck=deck, ordered_players=ordered_players
        )

        state.apply_action_card_penalty


class MatchState(db.Entity):
    current_turn = Required(int, default=0)
    prev_turn = Required(int, default=0)
    ordered_players = Required(StrArray)
    acumulator = Required(int, default=0)
    color = Optional(CardColor)
    direction = Required(Direction, default=Direction.RIGHT)
    match = Required(Match)
    winner = Optional(str)
    deck = Required(IntArray)
    pot = Required(IntArray)

    @property
    def top_card(self):
        return self.pot[-1]

    @property
    def length(self):
        return len(self.ordered_players)

    @property
    def steal_pot(self):
        top_card = self.pot.pop()
        new_deck = self.pot[:]
        random.shuffle(new_deck)
        self.pot = [top_card]
        return new_deck

    @property
    def apply_action_card_penalty(self):
        card_type = CARDS[self.top_card]["type"]

        if card_type == CardType.REVERSE:
            self.direction = self.reverse()

        if card_type == CardType.JUMP:
            self.next_turn(1)

        if card_type == CardType.TAKE_TWO:
            self.acumulator += 2

        if card_type == CardType.WILDCARD:
            self.color = CardColor.START

    @property
    def get_prev_turn(self):
        return self.ordered_players[self.prev_turn]

    @property
    def get_current_turn(self):
        return self.ordered_players[self.current_turn]

    @property
    def reverse(self):
        self.direction = (
            Direction.RIGHT if self.direction == Direction.RIGHT else Direction.LEFT
        )

    def next_turn(self, steps: int = 1):
        self.prev_turn = self.current_turn
        self.current_turn = (self.current_turn + (self.direction * steps)) % self.length

    def steal(self):
        if len(self.deck) < 1 or len(self.deck) < self.acumulator:
            self.deck = self.steal_pot

        quantity = max(self.acumulator, 1)

        if quantity > 1:
            self.acumulator = 0
            self.next_turn(1)
        else:
            self.acumulator += 1

        return [self.deck.pop() for _ in range(quantity)]


def open_database(filename):
    db.bind("sqlite", filename, create_db=True)
    db.generate_mapping(create_tables=True)


# When testing (pytest), it gets set to TESTING and creates a database in RAM memory
RUNNING_ENVIRONMENT = getenv("DB_ENV", "DEPLOYMENT")
if RUNNING_ENVIRONMENT == "TESTING":
    open_database(":sharedmemory:")
else:
    open_database("database.sqlite")
