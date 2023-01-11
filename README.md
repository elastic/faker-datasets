# Build [Faker](https://github.com/joke2k/faker#readme) providers based on datasets

`faker-datasets` offers a building block for seeding the data generation
with existing data.

You can create simple providers picking a random entry from a tailored dataset or
assemble complex ones where you generate new combinations from more datasets,
all this while keeping an eye on speed and memory consumption.

Let's see how to.

# Crash course

We'll use the wonderful [Countries State Cities DB](https://github.com/dr5hn/countries-states-cities-database)
maintained by [Darshan Gada](https://github.com/dr5hn). Download the
[cities](https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/v1.9/cities.json) and the
[countries](https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/v1.9/countries.json) datasets.

## Basic random picker

`Cities` generates a city by randomly picking an entry in the cities
dataset. Here the dataset is named `cities`, the dataset file is
`cities.json` (adjust to the actual path of the file saved earlier)
and the picker, the method to get a random city, is named `city`.

How we define it in file `cities_provider.py`:

```python
from faker_datasets import Provider, add_dataset

@add_dataset("cities", "cities.json", picker="city")
class Cities(Provider):
    pass
```

How we could use it to generate 10 cities:

```python
from faker import Faker
from cities_provider import Cities

fake = Faker()
fake.add_provider(Cities)

for _ in range(10):
    # Use of the picker named in @add_dateset
    city = fake.city()
    print("{name} is in {country_name}".format(**city))
```

One of the many possible outputs:

```
Poiana Cristei is in Romania
Codosera La is in Spain
Jeremoabo is in Brazil
Rodrígo M. Quevedo is in Mexico
Cary is in United States
Locking is in United Kingdom
Mezinovskiy is in Russia
Nesoddtangen is in Norway
Zalesnoye is in Ukraine
Cefa is in Romania
```

Because the data generation is a pseudo-random process, every execution outputs
different results. If you want reproducible outputs, you have to seed the Faker
generator as documented [here](https://faker.readthedocs.io/en/master/index.html#seeding-the-generator).

## Customize the random picker

`CitiesEx` is functionally identical to `Cities` but shows how to define
the picker by yourself. Here `picker=` is gone from the parameters of
`@add_dataset` but a new `city` method is defined.

```python
from faker_datasets import Provider, add_dataset, with_datasets

@add_dataset("cities", "cities.json")
class CitiesEx(Provider):

    @with_datasets("cities")
    def city(self, cities):
        return self.__pick__(cities)
```

Note how the `city` method is decorated with `@with_datasets("cities")`
and how, consequently, it receives the said dataset as parameter.
The call to `__pick__` just selects a random entry from `cities`.


## Matching a criterium

`CitiesFromCountry` exploits the custom picker to return only cities from a
given country. A first implementation could just discard cities from any
other country, getting slower with increasing bad luck.

```python
from faker_datasets import Provider, add_dataset, with_datasets

@add_dataset("cities", "cities.json")
class CitiesFromCountry(Provider):

    @with_datasets("cities")
    def city(self, cities, country_name):
        while True:
            city = self.__pick__(cities)
            if city["country_name"] == country_name:
                return city
```

It's better to limit to the number of attempts though otherwise if
`country_name` is misspelled the picker would enter in an infinite loop.

```python
from faker_datasets import Provider, add_dataset, with_datasets

@add_dataset("cities", "cities.json")
class CitiesFromCountry(Provider):

    @with_datasets("cities")
    def city(self, cities, country_name, max_attempts=10000):
        while max_attempts:
            city = self.__pick__(cities)
            if city["country_name"] == country_name:
                return city
            max_attempts -= 1
        raise ValueError("Run out of attempts")
```

Or, with same results, use the `match=` and `max_attempts=`
parameters of `__pick__`.

```python
from faker_datasets import Provider, add_dataset, with_datasets

@add_dataset("cities", "cities.json")
class CitiesFromCountry(Provider):

    @with_datasets("cities")
    def city(self, cities, country_name):
        # match tells to __picker__ whether the city is good or not
        match = lambda city: city["country_name"] == country_name
        return self.__pick__(cities, match=match, max_attempts=10000)
```

If you know ahead which country you are interested in, say Afghanistan,
you can use the `@with_match` picker decorator. It produces a new index
of only matching entries and the picking speed is again constant and
independent from bad luck.

```python
from faker_datasets import Provider, add_dataset, with_datasets, with_match

@add_dataset("cities", "cities.json")
class CitiesFromCountry(Provider):

    @with_datasets("cities")
    @with_match(lambda city: city["country_name"] == "Afghanistan")
    def afghan_city(self, cities):
        return self.__pick__(cities)
```

At such conditions though it's maybe better to massage your dataset and
leave only the entries matching your criteria.

## Using multiple datasets

`CitiesAndCountries` fuses two datasets for more advanced matches. Note
how `@add_dataset` makes multiple datasets available to the provider
and `@with_datasets` passes them to the given picker.

```python
from faker_datasets import Provider, add_dataset, with_datasets, with_match

@add_dataset("cities", "cities.json")
@add_dataset("countries", "countries.json")
class CitiesAndCountries(Provider):

    @with_datasets("cities", "countries")
    def city_by_region(self, cities, countries, region):
        def match(city):
            # Given a city, find its country info in the countries dataset
            country = next(country for country in countries if country["name"] == city["country_name"])
            # Check that the country is in the region of interest
            return country["region"] == region
        return self.__pick__(cities, match=match, max_attempts=10000)
```

The picker performs the data mix and match so that the region request
is satisfied or an error is signaled.

## Summary

You use `@add_dataset` to attach a dataset to your provider, if you specify
a `picker=` parameter you'll get for free a random picker of entries.
The more datasets you need, the more `@add_dataset` you can use.

If you have special needs you can define the pickers for yourself, each
using what datasets are most appropriate among those made available with
`@add_dataset`. You can add as many pickers as you need.

A picker can use `match=` and `max_attempts=` to make the generation respect
some useful criteria.
