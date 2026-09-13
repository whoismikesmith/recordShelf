from recordshelf.models import Release
from recordshelf.search import best_match, matches


def rel(iid: int, artist: str, title: str) -> Release:
    return Release(instance_id=iid, release_id=iid, artist=artist, artist_sort=artist, title=title)


def test_search_ignores_accents_both_ways():
    touche = rel(1, "Touché Amoré", "Parting the Sea Between Brightness and Me")
    sigur = rel(2, "Sigur Rós", "( )")
    assert matches(touche, "touche amore") and matches(touche, "TOUCHÉ amore")
    assert matches(sigur, "sigur ros") and not matches(sigur, "sigur rust")
    assert matches(rel(3, "Beyonce", "Lemonade"), "beyoncé")
    assert best_match([sigur, touche], "touche amore parting") is touche
