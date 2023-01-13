from functools import partialmethod, wraps
from pathlib import Path

from faker.providers import BaseProvider

__version__ = "0.1.0"


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
    max = len(dataset) - 1
    if not match:
        return dataset[faker.random_int(0, max)]
    while max_attempts:
        entry = dataset[faker.random_int(0, max)]
        if match(entry):
            return entry
        max_attempts -= 1
    raise ValueError("Run out of attempts")


class Provider(BaseProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # At the first instantiation, likely the only one, propagate
        # the datasets to all the decorated methods needing them.
        if hasattr(self.__class__, "__datasets__"):
            for member in self.__class__.__dict__.values():
                if hasattr(member, "set_datasets"):
                    member.set_datasets(self.__class__.__datasets__)

            # Pickers and decorated methods have a reference to the datasets of
            # their interest, let's drop all the unused others and free memory.
            del self.__class__.__datasets__


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
            args = func.datasets + args
            return func(faker, *args, **kwargs)

        def set_datasets(datasets):
            try:
                func.datasets = tuple(datasets[name] for name in self.names)
            except KeyError as e:
                raise ValueError(f"dataset not found: '{e.args[0]}'") from None
            if hasattr(func, "set_datasets"):
                func.set_datasets(datasets)

        _func.set_datasets = set_datasets
        return _func


class with_match:
    def __init__(self, match):
        self.match = match

    def __call__(self, func):
        @wraps(func)
        def _func(faker, *args, **kwargs):
            args = func.datasets + args[len(func.datasets) :]
            return func(faker, *args, **kwargs)

        def set_datasets(datasets):
            if not hasattr(_func, "datasets"):
                raise ValueError("Use @with_datasets first")
            func.datasets = tuple([x for x in d if self.match(x)] for d in _func.datasets)
            if hasattr(func, "set_datasets"):
                func.set_datasets(datasets)

        _func.set_datasets = set_datasets
        return _func
