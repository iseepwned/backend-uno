from pony.orm import db_session, TransactionIntegrityError, CacheIndexError
from ..models.models import Player
from utils import errors
from fastapi import status


@db_session
def create_player_or_400(player_name: str) -> int:
    try:
        player = Player(name=player_name)
        player.flush()
        return player.player_id

    except (TransactionIntegrityError, CacheIndexError):
        errors.throw(status.HTTP_400_BAD_REQUEST, errors.PLAYER_EXISTS)

    except Exception:
        errors.throw(
            status.HTTP_500_INTERNAL_SERVER_ERROR, errors.INTERNAL_ERROR_CREATING_PLAYER
        )


@db_session
def get_player_by_id(player_id: int) -> Player:
    return Player.get(player_id=player_id)
