"""
Django Model Factories for PisteMaster
Uses factory-boy's DjangoModelFactory to create test data for Django models.
"""

from datetime import date, timedelta

import factory
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyDate

from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from backend.apps.users.models import User


class UserFactory(DjangoModelFactory):
    """Factory for creating User Django model instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    role = FuzzyChoice(choices=["ADMIN", "SCHEDULER"])
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("testpassword123")


class DjangoTournamentFactory(DjangoModelFactory):
    """Factory for creating DjangoTournament model instances."""

    class Meta:
        model = DjangoTournament
        skip_postgeneration_save = True

    tournament_name = Faker("company")
    start_date = FuzzyDate(start_date=date.today(), end_date=date.today() + timedelta(days=30))
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=7))
    status = FuzzyChoice(choices=["PLANNING", "REGISTRATION_OPEN", "REGISTRATION_CLOSED", "ONGOING", "COMPLETED", "CANCELLED"])
    organizer = Faker("company")
    location = Faker("city")
    created_by = SubFactory(UserFactory)

    @factory.post_generation
    def schedulers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.schedulers.add(user)


class DjangoFencerFactory(DjangoModelFactory):
    """Factory for creating DjangoFencer model instances."""

    class Meta:
        model = DjangoFencer

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    display_name = factory.LazyAttribute(lambda obj: f"{obj.last_name} {obj.first_name}")
    gender = FuzzyChoice(choices=["MEN", "WOMEN", "MIXED", "OPEN"])
    country_code = Faker("country_code")
    birth_date = FuzzyDate(start_date=date(1970, 1, 1), end_date=date(2005, 12, 31))
    fencing_id = factory.LazyFunction(lambda: f"FEN{FuzzyInteger(100000, 999999).fuzz()}")
    current_ranking = FuzzyInteger(1, 1000)
    primary_weapon = FuzzyChoice(choices=["FOIL", "EPEE", "SABRE"])
