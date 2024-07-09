from pony.orm import db_session, ObjectNotFound
from fastapi import Body, status
from view_entities.match_view_entities import NewMatch, JoinMatch, ChangeColor
from database.dao.match_dao import get_match_by_id
from database.models.models import Match, Player
from database.models.enums import CardColor, CardType
from exceptions import match_exceptions, player_exceptions
from . import player_validators
from typing import Annotated
from view_entities.match_view_entities import PlayCard
from deserializers.match_deserializers import cards_deserializer
from utils import errors


def match_name_validator(match_name: str):
    if len(match_name) < 3 or len(match_name) > 16:
        errors.throw(status.HTTP_400_BAD_REQUEST, errors.INVALID_MATCH_NAME_LENGTH)


def new_match_validator(match: NewMatch):
    match_name_validator(match.match_name)
    player_validators.player_name_validator(match.creator_name)


@db_session
def join_match_validator(join: JoinMatch):
    player_validators.player_name_validator(join.player_name)


@db_session
def match_exists_validator(match_id: int):
    try:
        Match[match_id]
    except ObjectNotFound:
        raise match_exceptions.NOT_EXISTENT_MATCH


@db_session
def match_started_validator(match_id: int):
    match = Match[match_id]
    if match.started:
        raise match_exceptions.MATCH_ALREADY_STARTED


@db_session
def match_not_started_validator(match_id: int):
    match = Match[match_id]
    if not match.started:
        raise match_exceptions.MATCH_NOT_STARTED

@db_session
def turn_validator(match_id: int, player_id: int):
    current_turn = Match[match_id].state.get_current_turn
    player_name = Player[player_id].name

    if current_turn != player_name:
        raise match_exceptions.NOT_YOUR_TURN


@db_session
def player_in_match_validator(match_id: int, player_id: int):
    player = Player[player_id]
    players=[p.name for p in Match[match_id].players]

    if player.name not in players:
        raise player_exceptions.PLAYER_NOT_IN_MATCH


@db_session
def card_in_hand_validator(player_id: int, card_id: int):
    hand = Player[player_id].hand
    if card_id not in hand:
        raise player_exceptions.CARD_NOT_FOUND


@db_session
def color_validator(match_id: int):
    # El jugador primero debe hacer el cambio de color
    color = Match[match_id].state.color
    if color and color in [CardColor.WILDCARD, CardColor.START]:
        raise player_exceptions.NO_COLOR_CHOSEN_BEFORE_PLAY


def is_valid_card_for_play(card: dict, pot: dict, acumulator, color: CardColor | None) -> bool:
    if card["type"] in [CardType.WILDCARD, CardType.TAKE_FOUR_WILDCARD]:
        return True
    
    if pot["type"] == CardType.TAKE_FOUR_WILDCARD:
        if acumulator > 1 :
            if card["type"] == CardType.TAKE_TWO:
                return card["color"] == pot["color"]
            else:
                return False
    
    if pot["type"] == CardType.NUMBER:
        if card["type"] == CardType.NUMBER:
            return card["color"] == pot["color"] or card["number"] == pot["number"]
        else: 
            return card["color"] == pot["color"]

    if pot["type"] == CardType.TAKE_TWO:
        if acumulator > 1:
            return card["type"] == CardType.TAKE_TWO
    
    if pot["type"] in [CardType.TAKE_TWO, CardType.REVERSE, CardType.JUMP]:
        return card["type"] == pot["type"] or card["color"] == pot["color"]
    
    if color:
        return card["color"] == color
    
    return False



@db_session
def start_match_validator(player_id: Annotated[int, Body(embed=True)], match_id: int):
    match_exists_validator(match_id)
    match_started_validator(match_id)
    player_validators.player_exists_validator(player_id)
    player_validators.is_creator_validator(player_id)


@db_session
def follow_match_validator(match_id: int, player_id: int) -> bool:
    match = get_match_by_id(match_id)
    if not match:
        return False

    player = Player.get(player_id=player_id, match=match)
    if not player:
        return False

    return True


@db_session
def actions_validator(match_id: int, player_id: int):
    match_exists_validator(match_id)
    match_not_started_validator(match_id)
    player_validators.player_exists_validator(player_id)
    player_in_match_validator(match_id, player_id)


@db_session
def play_card_validator(match_id: int, payload: PlayCard):
    actions_validator(match_id, payload.player_id)
    turn_validator(match_id, payload.player_id)
    color_validator(match_id)
    card_in_hand_validator(payload.player_id, payload.card_id)

    # Chequeamos si la carta que el jugador quiere jugar es la ultima carta que robo
    state = Match[match_id].state
    if state.acumulator == 1:
        player = Player[payload.player_id]
        last_card_played = player.hand[-1]

        if payload.card_id != last_card_played:
            raise player_exceptions.UNPLAYED_STOLEN_CARD

    card = cards_deserializer([payload.card_id])[0]
    pot = cards_deserializer([state.top_card])[0]

    # Chequeamos si la carta puede ser tirada al pozo
    if not is_valid_card_for_play(card, pot,state.acumulator, state.color):
        raise player_exceptions.INVALID_PLAYED_CARD


@db_session
def steal_card_validator(match_id: int, player_id: Annotated[int, Body(embed=True)]):
    actions_validator(match_id, player_id)
    turn_validator(match_id, player_id)
    color_validator(match_id)

    # Chequeamos que el jugador no vuelva a robar otra carta si ya lo hizo
    if Match[match_id].state.acumulator == 1:
        raise player_exceptions.ALREADY_TOOK_CARD


@db_session
def next_turn_validator(match_id: int, player_id: Annotated[int, Body(embed=True)]):
    actions_validator(match_id, player_id)
    turn_validator(match_id, player_id)
    color_validator(match_id)

    # Chequeamos si el jugador hizo una jugada antes de pasar el turno
    if Match[match_id].state.acumulator != 1:
        raise player_exceptions.NOT_A_PLAY_WAS_MADE


@db_session
def change_color_validator(match_id: int, payload: ChangeColor):
    actions_validator(match_id, payload.player_id)
    turn_validator(match_id, payload.player_id)

    # Chequear si el color es valido
    if payload.color not in CardColor.__members__.values():
        raise player_exceptions.INVALID_COLOR

    color = Match[match_id].state.color
    if color in [CardColor.START, CardColor.WILDCARD]:
        return

    # Chequear si ya hubo cambio de color
    if color:
        raise player_exceptions.INVALID_COLOR_CHANGE_EXCEPTION


@db_session
def leave_validator(match_id: int, player_id: Annotated[int, Body(embed=True)]):
    match_exists_validator(match_id)
    player_validators.player_exists_validator(player_id)
    player_in_match_validator(match_id, player_id)


@db_session
def uno_validator(match_id: int, player_id: Annotated[int, Body(embed=True)]):
    actions_validator(match_id, player_id)

    player = Player[player_id]
    if len(player.hand) > 1:
        raise player_exceptions.MULTIPLE_CARDS_UNO
    if player.uno:
        raise player_exceptions.ALREADY_SONG_UNO


@db_session
def play_again_validator(match_id: int, player_id: Annotated[int, Body(embed=True)]):
    actions_validator(match_id, player_id)
    player_validators.is_creator_validator(player_id)

    state = Match[match_id].state
    if not state.winner:
        raise player_exceptions.NO_UNO
