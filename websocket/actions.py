from pony.orm import db_session
from database.models.models import Match, Player
from database.models.enums import CardType, CardColor
from deserializers.match_deserializers import cards_deserializer
from websocket import messages
from utils.match_utils import lobbys


@db_session
async def start(match_id: int):
    match = Match[match_id]
    state = match.state
    curr_turn = state.get_current_turn
    prev_turn = state.get_prev_turn
    pot = cards_deserializer([state.top_card])[0]
    pot_type = pot["type"]
    lobby = lobbys[match_id]

    # Envía un mensaje de inicio del juego a cada jugador
    for player in match.players:
        hand = cards_deserializer(player.hand)
        await lobby.send_personal_message(
            messages.start(hand, player.name, state.ordered_players, pot, curr_turn), player.name
        )

    if pot_type == CardType.TAKE_TWO:
        player = Player.get(name=prev_turn)
        #Steal pasa el turno
        cards = state.steal()
        curr_turn = state.get_current_turn
        prev_turn = state.get_prev_turn
        player.hand.extend(cards)

        await lobby.send_personal_message(messages.take(curr_turn, cards), prev_turn)
        await lobby.broadcast(messages.take_all(prev_turn, curr_turn, 2), prev_turn)



@db_session
async def play_card(match_id: int, card: dict = None, cards: list = None):
    state = Match[match_id].state
    lobby = lobbys[match_id]
    curr_turn = state.get_current_turn
    prev_turn = state.get_prev_turn

    if cards:
        await lobby.send_personal_message(messages.not_uno(cards, curr_turn), prev_turn)
        await lobby.broadcast(messages.not_uno_all(curr_turn, prev_turn, len(cards)), prev_turn)
    else:
        if card["type"] in ["WILDCARD", "TAKE_FOUR_WILDCARD"]:
            await lobby.broadcast(messages.card_played(card, curr_turn, curr_turn))
        else:
            await lobby.broadcast(messages.card_played(card, curr_turn, prev_turn))

    if state.winner:
        await lobby.broadcast(messages.winner(prev_turn))


@db_session
async def steal_card(match_id: int, cards: list):
    state = Match[match_id].state
    curr_turn = state.get_current_turn
    prev_turn = state.get_prev_turn
    lobby = lobbys[match_id]
    length = len(cards)

    if length > 1:
        await lobby.send_personal_message(messages.take(curr_turn, cards), prev_turn)
        await lobby.broadcast(
            messages.take_all(prev_turn, curr_turn, length), prev_turn
        )
    else:
        await lobby.send_personal_message(messages.steal(cards), curr_turn)
        await lobby.broadcast(messages.steal_all(), curr_turn)


@db_session
async def next_turn(match_id: int):
    curr_turn = Match[match_id].state.get_current_turn
    await lobbys[match_id].broadcast(messages.next_turn(curr_turn))


@db_session
async def change_color(match_id: int, color: str):
    state = Match[match_id].state

    message_to_broadcast = {
        "action": "CHANGE_COLOR",
        "color": color,
        "player": state.get_prev_turn,
    }
    if state.color != CardColor.START:
        message_to_broadcast["turn"] = state.get_current_turn

    await lobbys[match_id].broadcast(message_to_broadcast)


@db_session
async def leave(match_id: int, player_name: str):
    match = Match.get(match_id=match_id)
    lobby = lobbys[match_id]

    if not match:
        await lobby.broadcast({"action": "LOBBY_DESTROY"})
        await lobby.destroy()
        return

    if match.started:
        state = match.state
        curr_turn = state.get_current_turn
        prev_turn = state.get_prev_turn
        await lobby.broadcast(messages.leave(player_name))
        if state and state.length == 1:
            await lobby.broadcast({"action": "MATCH_OVER"}, player_name)

        if state and prev_turn == player_name:
            await lobby.broadcast(messages.next_turn(curr_turn), player_name)
    else:
        await lobby.broadcast(messages.leave(player_name))
  
    await lobby.disconnect(player_name)
