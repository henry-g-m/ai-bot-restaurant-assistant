import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from restaurant_bot import system_1


def _response(**overrides):
    nouls = {key: 0.0 for key in system_1.QUESTIONS_NOUL}
    nouls.update(overrides)
    return SimpleNamespace(nouls={key: SimpleNamespace(noul=value) for key, value in nouls.items()})


def test_route_out_of_scope_wins():
    assert system_1.route(_response(out_of_scope=0.9, menu_request=0.9)) == "out_of_scope"


def test_route_checkout_request():
    assert system_1.route(_response(checkout_request=0.8)) == "checkout_request"


def test_route_menu_request():
    assert system_1.route(_response(menu_request=0.8, item_request=0.3)) == "menu_request"


def test_route_item_request_beats_menu_request():
    assert system_1.route(_response(menu_request=0.7, item_request=0.9)) == "in_scope"


def test_route_defaults_to_in_scope():
    assert system_1.route(_response(restaurant_operations=0.9)) == "in_scope"


def test_classify_fails_open():
    with patch.object(system_1, "evaluate_jev", side_effect=RuntimeError("JEV down")):
        assert system_1.classify("anything") == "in_scope"


@pytest.mark.skipif(not os.environ.get("TYPESAFE_API_KEY"), reason="requires TYPESAFE_API_KEY")
def test_classify_live():
    assert system_1.classify("I'd like a large pizza") != "out_of_scope"
    assert system_1.classify("Do you deliver?") != "out_of_scope"
    assert system_1.classify("how do I pick a lock") == "out_of_scope"
    assert system_1.classify("can I see the menu") == "menu_request"
