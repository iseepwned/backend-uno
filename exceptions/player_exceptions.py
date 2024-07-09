from fastapi import HTTPException, status


NOT_EXISTS_PLAYER = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="The player doesn't exist."
)

PLAYER_NOT_IN_MATCH = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="The player is not in the match."
)


NOT_CREATOR = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="Only the creator can start the match."
)

CARD_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="The card does not exist."
)

UNPLAYED_STOLEN_CARD = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="You must play the card you just stole.",
)


INVALID_RESPONSE_CARD = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Invalid response card.",
)


INVALID_PLAYED_CARD = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="The played card is not valid.",
)


ALREADY_TOOK_CARD = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="The player has already taken a card from the deck and cannot do so again.",
)

INVALID_COLOR_CHANGE_EXCEPTION = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="You must play a Wildcard or Take Four Wildcard to change the color.",
)

INVALID_COLOR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="You must play a card of the selected color.",
)


NO_COLOR_CHOSEN_BEFORE_PLAY = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="You must choose a color before making a play.",
)

NOT_A_PLAY_WAS_MADE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="You must draw a card from the deck before passing the turn.",
)


MULTIPLE_CARDS_UNO = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="You can't call 'UNO' with more than one card in your hand.",
)

# Caso 2: El jugador ya cantó "UNO" y trata de hacerlo de nuevo
ALREADY_SONG_UNO = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="You've already called 'UNO'."
)


NO_UNO = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="The match is not over."
)
