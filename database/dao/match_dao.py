from pony.orm import db_session, TransactionIntegrityError
from ..models.models import Match, Player
from .player_dao import create_player_or_400
from exceptions import match_exceptions
from ..models.enums import CardColor, CardType
from utils import errors
from fastapi import status


@db_session
def create_match_or_400(match_name: str, creator_id: int) -> int:
    try:
        creator = Player[creator_id]
        match = Match(name=match_name, creator=creator, players=[creator])
        match.flush()
        return match.match_id

    except TransactionIntegrityError:
        errors.throw(status.HTTP_400_BAD_REQUEST, errors.MATCH_EXISTS)

    except Exception:
        errors.throw(
            status.HTTP_500_INTERNAL_SERVER_ERROR, errors.INTERNAL_ERROR_CREATING_MATCH
        )


@db_session
def create_new_match(match_name: str, creator_name: str) -> tuple[int, int]:
    creator_id = create_player_or_400(creator_name)
    match_id = create_match_or_400(match_name, creator_id)
    return match_id, creator_id


@db_session
def get_match_by_id(match_id: int):
    return Match.get(match_id=match_id)


@db_session
def get_match_by_code(code: str) -> Match:
    return Match.get(code=code)


@db_session
def join_update(player_name: str, code: str) -> tuple[int, int]:
    # Chequeamos si la partida existe
    match = get_match_by_code(code)
    if not match:
        raise match_exceptions.NOT_EXISTENT_MATCH

    # Chequeamos si la partida esta iniciada
    if match.started:
        raise match_exceptions.MATCH_ALREADY_STARTED

    # Chequeamos si la partida esta llena
    if match.max_players == len(match.players):
        raise match_exceptions.MATCH_FULL

    # Agregamos el jugador a la partida
    player = Player[create_player_or_400(player_name)]
    match.players.add(player)

    return match.match_id, player.player_id


@db_session
def play_card_update(match_id: int, player_id: int, card: dict):
    state = Match[match_id].state
    player = Player[player_id]
    card_type = card["type"]

    if len(player.hand) == 1:
        if player.uno:
            state.winner = player.name
        else:
            cards = state.steal() + state.steal()
            player.hand.extend(cards)
            state.next_turn(1)
            return cards

    # Ahora la carta no pertenece al jugador sino al pozo
    state.pot.append(card["id"])
    player.hand.remove(card["id"])

    # El jugador tiro la carta robada, ajustamos el acumulador
    if state.acumulator == 1:
        state.acumulator = 0

    if state.color:
        state.color = None

    # Ajustamos acumulador para TAKE_TWO o TAKE_FOUR_WILDCARD
    if card_type == CardType.TAKE_TWO:
        state.acumulator += 2
    elif card_type == CardType.TAKE_FOUR_WILDCARD:
        state.acumulator += 4
        state.color = CardColor.WILDCARD
        # Retornamos porque el jugador tiene que cambiar de color, por lo tanto sigue teniendo el turno
        return

    if card_type == CardType.WILDCARD:
        state.color = CardColor.WILDCARD
        return

    # Cambiar dirección para REVERSE
    if card_type == CardType.REVERSE:
        state.reverse

    # Pasamos el turno
    if card_type == CardType.JUMP:
        state.next_turn(2)
    else:
        state.next_turn(1)


@db_session
def steal_card_update(match_id: int, player_id: int) -> list:
    steal_cards = Match[match_id].state.steal()
    player = Player[player_id]
    player.hand.extend(steal_cards)

    if player.uno:
        player.uno = False

    return steal_cards


@db_session
def update_leave_lobby(match_id: int, player_id: int):
    player = Player[player_id]
    match = Match[match_id]

    if player.creator:
        match.delete()
    else:
        player.delete()


@db_session
def update_leave_match(match_id: int, player_id: int):
    player = Player[player_id]
    match = Match[match_id]

    if player.creator:
        match.delete()
    else:
        state = match.state
        if len(state.ordered_players) == 2:
            state.delete()
            match.started = False
        if player.name == state.get_current_turn:
            state.next_turn(1)

        state.ordered_players.remove(player.name)
        state.deck.extend(player.hand)
        player.delete()
