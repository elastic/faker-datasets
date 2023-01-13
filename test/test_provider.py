import gc
import os
import re
from pathlib import Path

import pytest
from faker import Faker

from faker_datasets import Provider, add_dataset, with_datasets, with_match


@pytest.fixture
def books_dataset():
    return Path(__file__).parent / "testdata" / "books.json"


@pytest.fixture
def movies_dataset():
    return Path(__file__).parent / "testdata" / "movies.json"


@pytest.fixture
def fake(request, books_dataset, movies_dataset):
    @add_dataset("books", books_dataset, picker="book", root=".entries")
    @add_dataset("movies", movies_dataset, picker="movie", root=".entries")
    class TestProvider(Provider):
        @with_datasets("books", "movies")
        def book_or_movie(self, books, movies, *, before=None):
            match = None if before is None else lambda x: "year" in x and x["year"] < before
            return self.__pick__(books + movies, match=match)

        @with_datasets("books")
        @with_match(lambda x: "year" in x and x["year"] == 1954)
        def book_made_in_1954(self, books):
            return self.__pick__(books)

    # throw the first instance away, the second must work as well
    _fake = Faker()
    _fake.add_provider(TestProvider)

    fake = Faker()
    fake.add_provider(TestProvider)
    fake.seed_instance(request.node.name)
    return fake


def test_dataset(fake):
    for item in [
        {"title": "The Robots of Dawn", "author": "Isaac Asimov", "year": 1983},
        {"title": "The Robots of Dawn", "author": "Isaac Asimov", "year": 1983},
        {"title": "I Promessi Sposi", "author": "Alessandro Manzoni"},
        {"title": "Odyssey", "author": "Homer"},
        {"title": "Decameron", "author": "Giovanni Boccaccio"},
        {"title": "Robots and Empire", "author": "Isaac Asimov", "year": 1985},
        {"title": "Divine Comedy", "author": "Dante Alighieri"},
    ]:
        assert item == fake.book()

    for item in [
        {"title": "The Shining", "genre": ["drama", "horror"], "year": 1980},
        {"title": "Ice Age", "genre": ["animation", "adventure", "comedy"], "year": 2002},
        {"title": "The Terminal", "genre": ["comedy", "drama", "romance"], "year": 2004},
        {"title": "M*A*S*H*", "genre": ["comedy", "drama", "war"], "year": 1970},
        {"title": "Star Trek", "genres": ["action", "adventure", "sci-fi"], "year": 1966},
        {"title": "The Shining", "genre": ["drama", "horror"], "year": 1980},
        {"title": "Star Trek", "genres": ["action", "adventure", "sci-fi"], "year": 1966},
    ]:
        assert item == fake.movie()

    for item in [
        {"title": "Odyssey", "author": "Homer"},
        {"title": "I Promessi Sposi", "author": "Alessandro Manzoni"},
        {"title": "I Promessi Sposi", "author": "Alessandro Manzoni"},
        {"title": "Decameron", "author": "Giovanni Boccaccio"},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Robots of Dawn", "author": "Isaac Asimov", "year": 1983},
        {"title": "I Promessi Sposi", "author": "Alessandro Manzoni"},
    ]:
        assert item == fake.book_or_movie()


def test_dataset_with_match(fake):
    for item in [
        {"title": "Star Trek", "genres": ["action", "adventure", "sci-fi"], "year": 1966},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "M*A*S*H*", "genre": ["comedy", "drama", "war"], "year": 1970},
        {"title": "Star Trek", "genres": ["action", "adventure", "sci-fi"], "year": 1966},
        {"title": "M*A*S*H*", "genre": ["comedy", "drama", "war"], "year": 1970},
        {"title": "Star Trek", "genres": ["action", "adventure", "sci-fi"], "year": 1966},
    ]:
        assert item == fake.book_or_movie(before=1975)

    for item in [
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
        {"title": "The Caves of Steel", "author": "Isaac Asimov", "year": 1954},
    ]:
        assert item == fake.book_made_in_1954()


def test_drop_unused_datasets():
    import psutil

    @add_dataset("alerts", Path(__file__).parent / "testdata" / "alerts.json")
    class TestProvider(Provider):
        pass

    fake = Faker()

    proc = psutil.Process(os.getpid())
    gc.collect()
    before = proc.memory_info().rss

    fake.add_provider(TestProvider)

    gc.collect()
    after = proc.memory_info().rss

    print(f"Memory release: {before} -> {after} (delta: {before - after})")
    assert before > after


def test_dataset_without_match(fake):
    match = lambda x: x.get("author", None) == "Francesco Petrarca"
    msg = "Run out of attempts"
    with pytest.raises(ValueError, match=re.escape(msg)):
        _ = fake.book(match=match, max_attempts=1)
        pytest.fail(f"Did not raise ValueError: {msg}")


def test_with_no_datasets(books_dataset):
    msg = "__init__() missing 1 required positional argument: 'name'"
    with pytest.raises(TypeError, match=re.escape(msg)) as exc:

        @add_dataset("books", books_dataset)
        class TestProvider(Provider):
            @with_datasets()
            def book(self, books):
                pass

        pytest.fail(f"Did not raise TypeError: {msg}")


def test_with_wrong_dataset(books_dataset):
    @add_dataset("books", books_dataset)
    class TestProvider(Provider):
        @with_datasets("movie")
        def book(self, books):
            pass

    fake = Faker()
    msg = "dataset not found: 'movie'"
    with pytest.raises(ValueError, match=re.escape(msg)) as exc:
        fake.add_provider(TestProvider)
        pytest.fail(f"Did not raise ValueError: {msg}")


def test_match_without_dataset(books_dataset):
    @add_dataset("books", books_dataset)
    class TestProvider(Provider):
        @with_match(lambda x: "year" in x and x["year"] == 1954)
        def book(self, books):
            pass

    fake = Faker()
    msg = "Use @with_datasets first"
    with pytest.raises(ValueError, match=re.escape(msg)) as exc:
        fake.add_provider(TestProvider)
        pytest.fail(f"Did not raise ValueError: {msg}")


def test_malformed_root(movies_dataset):
    for root in ("entries.", "ent..ries", ".entries[]genre", "entries[].genre"):
        msg = f"Malformed root: {root}"
        with pytest.raises(ValueError, match=re.escape(msg)) as exc:

            @add_dataset("books", movies_dataset, root=root)
            class TestProvider(Provider):
                pass

            pytest.fail(f"Did not raise ValueError: {msg}")
