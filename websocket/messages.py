from deserializers.match_deserializers import cards_deserializer


def join_message(player_name: str):
    return {"action": "JOIN", "player_name": player_name}


def start(hand: list, player_name:str,ordered_players:list, pot: list, turn: str) -> dict:
    return {"action": "START", "data": {"hand": hand, "player_name":player_name,"ordered_players":ordered_players, "pot": pot, "turn": turn}}


def not_uno(cards: list, turn: str) -> dict:
    cards_parse = cards_deserializer(cards)
    return {"action": "NOT_UNO", "cards": cards_parse, "turn": turn}


def not_uno_all(turn: str, player_name: str, length:int) -> dict:
    return {"action": "NOT_UNO", "turn": turn, "player_name": player_name, "length": length}


def uno(player_name: str) -> dict:
    return {"action": "UNO", "player_name": player_name}


def card_played(card: dict, turn: str, player_name: str) -> dict:
    return {"action": "PLAY_CARD", "player_name": player_name, "turn": turn, "pot": card}


def winner(player_name: str) -> dict:
    return {"action": "WINNER", "player_name": player_name}


def wildcard(player_name: str) -> dict:
    return {"action": "WILDCARD", "player_name": player_name}


def steal(cards: list) -> dict:
    return {"action": "STEAL", "cards": cards_deserializer(cards)}


def steal_all() -> dict:
    return {"action": "STEAL"}


def take(turn: str, cards: list) -> dict:
    return {"action": "TAKE", "turn": turn, "cards": cards_deserializer(cards)}


def take_all(player_name: str, turn: str, length: int) -> dict:
    return {"action": "TAKE", "player_name": player_name, "turn": turn, "length": length}


def jump(player_name: str, turn: str) -> dict:
    return {"action": "JUMP", "player_name": player_name, "turn": turn}


def leave(player_name: str):
    return {"action": "LEAVE", "player_name": player_name}


def next_turn(turn: str):
    return {"action": "NEXT_TURN", "turn": turn}


def change_color(color: str, turn: str):
    return {"action": "CHANGE_COLOR", "color": color, "turn": turn}
