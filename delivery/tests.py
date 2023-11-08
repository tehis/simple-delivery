from typing import Iterable, List, Tuple

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from delivery.models import Vendor, Order


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def vendors(db) -> Vendor:
    vendor1 = Vendor.objects.create(name='first_vendor')
    vendor2 = Vendor.objects.create(name='second_vendor')
    vendor3 = Vendor.objects.create(name='third_vendor')

    return vendor1, vendor2, vendor3



