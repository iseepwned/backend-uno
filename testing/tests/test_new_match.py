import pytest
from ..mocks import endpoints
from utils import errors
from view_entities.match_view_entities import *

url = "new-match"


@pytest.mark.asyncio
async def test_invalid_match_name_length():
    match = NewMatch(match_name="Ma", creator_name="Creator 1").model_dump()

    response = await endpoints.new_match(url, match)
    assert response.status_code == 400
    assert response.json()["detail"] == errors.INVALID_MATCH_NAME_LENGTH


@pytest.mark.asyncio
async def test_invalid_player_name_length():
    match = NewMatch(match_name="Match 1", creator_name="Cr").model_dump()

    response = await endpoints.new_match(url, match)
    assert response.status_code == 400
    assert response.json()["detail"] == errors.INVALID_PLAYER_NAME_LENGTH


@pytest.mark.asyncio
async def test_player_exists():
    match = NewMatch(match_name="Match 1", creator_name="Creator 1").model_dump()
    match2 = NewMatch(match_name="Match 2", creator_name="Creator 1").model_dump()

    await endpoints.new_match(url, match)
    response = await endpoints.new_match(url, match2)
    assert response.status_code == 400
    assert response.json()["detail"] == errors.PLAYER_EXISTS


@pytest.mark.asyncio
async def test_match_exists():
    match = NewMatch(match_name="Match 1", creator_name="Creator 1").model_dump()
    match2 = NewMatch(match_name="Match 1", creator_name="Creator 2").model_dump()

    await endpoints.new_match(url, match)
    response = await endpoints.new_match(url, match2)
    assert response.status_code == 400
    assert response.json()["detail"] == errors.MATCH_EXISTS


@pytest.mark.asyncio
async def test_success():
    match = NewMatch(match_name="Match 1", creator_name="Creator 1").model_dump()
    response = await endpoints.new_match(url, match)
    assert response.status_code == 201
