from database.models.models import CARDS
from pony.orm import db_session
from view_entities.match_view_entities import MatchInfo
from database.models.models import Match


@db_session
def match_deserializer(match_id: int, player_id: int):
    match = Match[match_id]

    return MatchInfo(
        match_id=match_id,
        player_id=player_id,
        name=match.name,
        code=match.code,
        creator=match.creator.name,
        min_players=match.min_players,
        max_players=match.max_players,
        started=match.started,
        players=[p.name for p in match.players],
    )


def cards_deserializer(cards: list) -> list:
    return [CARDS[card] for card in cards]
