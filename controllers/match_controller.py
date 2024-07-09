from pony.orm import db_session
from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, Body, Depends
from typing import Annotated
from database.models.models import Match, Player
from database.models.enums import CardColor
from database.dao.match_dao import (
    create_new_match,
    join_update,
    play_card_update,
    steal_card_update,
    update_leave_lobby,
    update_leave_match,
)
from validators.match_validators import (
    new_match_validator,
    join_match_validator,
    start_match_validator,
    follow_match_validator,
    next_turn_validator,
    play_card_validator,
    steal_card_validator,
    change_color_validator,
    leave_validator,
    uno_validator,
    play_again_validator,
)
from utils.match_utils import LobbyManager, lobbys
from view_entities.match_view_entities import (
    NewMatch,
    JoinMatch,
    MatchInfo,
    PlayCard,
    ChangeColor,
)
from deserializers.match_deserializers import match_deserializer, cards_deserializer
from websocket import messages, actions

match_controller = APIRouter()


@match_controller.post("/new-match", status_code=status.HTTP_201_CREATED)
async def create(match: NewMatch, _=Depends(new_match_validator)) -> MatchInfo:
    match_id, creator_id = create_new_match(match.match_name, match.creator_name)

    # Creamos el manejador de conexiones para websockets
    lobbys[match_id] = LobbyManager()

    # Retornamos la info del match deserializada
    return match_deserializer(match_id, creator_id)


@match_controller.post("/join-match", status_code=status.HTTP_201_CREATED)
async def join(join: JoinMatch, _=Depends(join_match_validator)) -> MatchInfo:
    match_id, player_id = join_update(join.player_name, join.code)

    await lobbys[match_id].broadcast(messages.join_message(join.player_name))

    # Retornamos la info del match deserializada
    return match_deserializer(match_id, player_id)


@match_controller.websocket("/ws/follow-lobby/{match_id}")
async def follow_lobby(websocket: WebSocket, match_id: int, player_id: int):
    if not follow_match_validator(match_id, player_id):
        await websocket.close()
        return
    try:
        with db_session:
            player_name = Player[player_id].name
            await lobbys[match_id].connect(player_name, websocket)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        return


@match_controller.put("/start-match/{match_id}", status_code=status.HTTP_200_OK)
async def start(
    player_id: Annotated[int, Body(embed=True)],
    match_id: int,
    _=Depends(start_match_validator),
):
    # Repartimos las cartas, creamos el mazo y pozo.
    with db_session:
        match = Match[match_id]
        match.start()

    await actions.start(match_id)


@match_controller.put("/play-card/{match_id}", status_code=status.HTTP_200_OK)
async def play_card(match_id: int, payload: PlayCard, _=Depends(play_card_validator)):
    card = cards_deserializer([payload.card_id])[0]
    cards = play_card_update(match_id, payload.player_id, card)
    await actions.play_card(match_id, card, cards)

    return True


@match_controller.put("/steal-card/{match_id}", status_code=status.HTTP_200_OK)
async def steal_card(
    match_id: int,
    player_id: Annotated[int, Body(embed=True)],
    _=Depends(steal_card_validator),
):
    cards = steal_card_update(match_id, player_id)

    await actions.steal_card(match_id, cards)


@match_controller.put("/next-turn/{match_id}", status_code=status.HTTP_200_OK)
async def next_turn(
    match_id: int,
    player_id: Annotated[int, Body(embed=True)],
    _=Depends(next_turn_validator),
):
    with db_session:
        state = Match[match_id].state
        state.next_turn(1)
        state.acumulator = 0

    await actions.next_turn(match_id)


@match_controller.put("/change-color/{match_id}", status_code=status.HTTP_200_OK)
async def change_color(
    match_id: int,
    payload: ChangeColor,
    _=Depends(change_color_validator),
):
    with db_session:
        # Para el caso inicial no deberia pasar el turno
        state = Match[match_id].state
        if state.color == CardColor.WILDCARD:
            state.next_turn(1)
        state.color = payload.color

    await actions.change_color(match_id, payload.color)


@match_controller.post("/leave/{match_id}", status_code=status.HTTP_200_OK)
async def leave(
    match_id: int,
    player_id: Annotated[int, Body(embed=True)],
    _=Depends(leave_validator),
):
    player = None
    with db_session:
        match = Match[match_id]
        player = Player[player_id].name

        if match.started:
            update_leave_match(match_id, player_id)
        else:
            update_leave_lobby(match_id, player_id)

    await actions.leave(match_id, player)


@match_controller.put("/uno/{match_id}", status_code=status.HTTP_200_OK)
async def uno(
    match_id: int,
    player_id: Annotated[int, Body(embed=True)],
    _=Depends(uno_validator),
):

    with db_session:
        player = Player[player_id]
        player.uno = True
        await lobbys[match_id].broadcast(messages.uno(player.name))


@match_controller.put("/play_again/{match_id}", status_code=status.HTTP_200_OK)
async def play_again(
    match_id: int,
    player_id: Annotated[int, Body(embed=True)],
    _=Depends(play_again_validator),
):

    with db_session:
        match = Match[match_id]
        match.state.delete()
        match.started = False
        for player in match.players:
            player.hand.clear()

    await lobbys[match_id].broadcast({"action": "PLAY_AGAIN"})
