from functools import partialmethod, wraps
from pathlib import Path

from faker.providers import BaseProvider

__version__ = "0.0.0"


def load_json(fp):
    import json

    return json.load(fp)


def load_dataset(filename):
    suffix = Path(filename).suffix[1:]
    with open(filename) as fp:
        if suffix == "json":
            return load_json(fp)
        else:
            raise ValueError("Unsupported format: %s", suffix)


def chroot(dataset, common_path, item_path=None):
    for part in common_path.split(".")[1:]:
        dataset = dataset[part]
    if item_path:
        item_path_parts = item_path.split(".")[1:]
        new_dataset = []
        for item in dataset:
            for part in item_path_parts:
                item = item[part]
            new_dataset.append(item)
        dataset = new_dataset
    return dataset


def dataset(filename, root):
    paths = root.split("[]")
    if not all(x.startswith(".") for x in paths if x):
        raise ValueError(f"Malformed root: {root}")
    if root != "." and root.endswith(".") or root.find("..") != -1 or len(paths) > 2:
        raise ValueError(f"Malformed root: {root}")
    dataset = load_dataset(filename)
    return dataset if root == "." else chroot(dataset, *paths)


def pick(faker, dataset, *, match=None, max_attempts=1000):
    if not match:
        return faker.random_element(dataset)
    while max_attempts:
        entry = faker.random_element(dataset)
        if match(entry):
            return entry
        max_attempts -= 1
    raise ValueError("Run out of attempts")


class Provider(BaseProvider):
    pass


class add_dataset:
    def __init__(self, name, filename, *, picker=None, root=None):
        self.name = str(name)
        self.picker = str(picker or "")
        self.dataset = dataset(filename, str(root or "."))

    def __call__(self, cls):
        if not hasattr(cls, "__pick__"):
            cls.__pick__ = pick
        if not hasattr(cls, "__datasets__"):
            cls.__datasets__ = {}
        cls.__datasets__[self.name] = self.dataset
        if self.picker:
            setattr(cls, self.picker, partialmethod(pick, self.dataset))
        return cls


class with_datasets:
    def __init__(self, name, *others):
        names = (name,) + others
        self.names = [str(name) for name in names]

    def __call__(self, func):
        @wraps(func)
        def _func(faker, *args, **kwargs):
            if not hasattr(func, "datasets"):
                func.datasets = tuple(faker.__datasets__[name] for name in self.names)
            args = func.datasets + args
            return func(faker, *args, **kwargs)

        return _func


class with_match:
    def __init__(self, match):
        self.match = match

    def __call__(self, func):
        @wraps(func)
        def _func(faker, *args, **kwargs):
            if not hasattr(func, "datasets"):
                if not hasattr(_func, "datasets"):
                    raise ValueError("Use with_datasets first")
                func.datasets = tuple([x for x in d if self.match(x)] for d in _func.datasets)
            args = func.datasets + args[len(func.datasets) :]
            return func(faker, *args, **kwargs)

        return _func
