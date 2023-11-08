from datetime import datetime, timedelta
from typing import List

import pytest
from django.urls import reverse
from pytz import timezone as tz
from rest_framework import status
from rest_framework.test import APIClient

from delivery.models import (Agent, DelayQueue, DelayReport, DelayStatus,
                             DeliveryStatus, Order, Trip, Vendor)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def vendors(db) -> Vendor:
    vendor1 = Vendor.objects.create(name='first_vendor')
    vendor2 = Vendor.objects.create(name='second_vendor')

    return vendor1, vendor2

@pytest.fixture
def orders(db, vendors):
    # now = datetime.now().replace(tzinfo=tz('UTC'))
    orders = []
    orders.append(Order.objects.create(vendor=vendors[0], delivery_time=datetime.now()+timedelta(days=1)))
    orders.append(Order.objects.create(vendor=vendors[0], delivery_time=datetime.now()-timedelta(minutes=5)))
    orders.append(Order.objects.create(vendor=vendors[0], delivery_time=datetime.now()-timedelta(minutes=5)))
    orders.append(Order.objects.create(vendor=vendors[1], delivery_time=datetime.now()-timedelta(minutes=5)))
    orders.append(Order.objects.create(vendor=vendors[1], delivery_time=datetime.now()-timedelta(minutes=5)))

    return orders


def test_announce_delay_with_wrong_data(client):
    data = {
        'malformed_order_id': 4
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_announce_delay_with_not_existing_order(db, client):
    data = {
        'order_id': 10
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_announce_delay_when_delivery_time_has_not_passed_yet(client, orders: List[Order]):
    data = {
        'order_id': orders[0].id
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED


def test_announce_delay_report_should_be_created_if_not_exists(client, orders: List[Order]):
    data = {
        'order_id': orders[1].id
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_200_OK
    assert DelayReport.objects.filter(order=orders[1]).exists()


def test_announce_delay_report_update_delay_if_report_exists_already(client, orders: List[Order]):
    report = DelayReport.objects.create(order=orders[1], delay=timedelta(minutes=1))

    data = {
        'order_id': orders[1].id
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_200_OK
    assert DelayReport.objects.get(pk=report.id).delay.min == timedelta(minutes=5).min


@pytest.mark.parametrize('queue', [True, False])
def test_announce_delay_place_in_queue_if_there_is_no_item_in_queue_or_all_of_them_have_resolved(
    client, orders: List[Order], queue
):
    if queue:
        report = DelayReport.objects.create(order=orders[1], delay=timedelta(minutes=1))
        DelayQueue(report=report,  status=DelayStatus.RESOLVED)

    data = {
        'order_id': orders[1].id
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_200_OK
    assert 'placed' in response.data['message']
    assert DelayQueue.objects.count() == 1


@pytest.mark.parametrize('delay_status', [DelayStatus.UNASSIGNED, DelayStatus.ASSIGNED])
def test_announce_delay_do_not_place_in_queue_if_previous_noes_has_not_resolved(
    client, orders: List[Order], delay_status
):
    report = DelayReport.objects.create(order=orders[1], delay=timedelta(minutes=1))
    DelayQueue.objects.create(report=report,  status=delay_status)

    data = {
        'order_id': orders[1].id
    }

    response = client.post(reverse('annouce-delay'), data=data)
    assert response.status_code == status.HTTP_200_OK
    assert 'already' in response.data['message']
    assert DelayQueue.objects.count() == 1


@pytest.mark.parametrize('delivery_status', [DeliveryStatus.ASSIGNED, DeliveryStatus.AT_VENDOR, DeliveryStatus.PICKED])
def test_announce_delay_update_delivery_time_if_trip_is_not_in_delivered_status(
    client, orders: List[Order], delivery_status
):
    Trip.objects.create(order=orders[1], status=delivery_status)
    old_time = orders[1].delivery_time.replace(tzinfo=tz('UTC'))

    data = {
        'order_id': orders[1].id
    }


    response = client.post(reverse('annouce-delay'), data=data)

    order = Order.objects.get(pk=orders[1].id)

    assert response.status_code == status.HTTP_200_OK
    assert (order.delivery_time - old_time).min >= timedelta(minutes=30).min
    assert response.data['new_delivery_time'] == order.delivery_time


def test_delay_queue_if_agent_does_not_exists(db, client):
    data = {
        'agent_id': 10
    }

    response = client.get(reverse('delay-queue'), data=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delay_queue_aggin_delay_only_if_delay_is_unassigned_in_ascending_order(client, orders):
    agent = Agent.objects.create(name='dummy')

    report = DelayReport.objects.create(order=orders[1], delay=timedelta(minutes=1))

    delay1 = DelayQueue.objects.create(report=report, status=DelayStatus.UNASSIGNED)
    delay2 = DelayQueue.objects.create(report=report, status=DelayStatus.ASSIGNED)
    delay3 = DelayQueue.objects.create(report=report, status=DelayStatus.RESOLVED)
    delay4 = DelayQueue.objects.create(report=report, status=DelayStatus.UNASSIGNED)

    params = {
        'agent_id': agent.id
    }

    response = client.get(reverse('delay-queue'), params)
    data = response.data

    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert data[0]['id'] == delay1.id
    assert data[1]['id'] == delay4.id


def test_get_report_per_vendor(client, orders):
    agent = Agent.objects.create(name='dummy')

    before_last_week = datetime.now() - timedelta(days=10)
    report1 = DelayReport.objects.create(order=orders[1], delay=timedelta(days=1), created_at=before_last_week)
    report2 = DelayReport.objects.create(order=orders[2], delay=timedelta(hours=10))
    report3 = DelayReport.objects.create(order=orders[3], delay=timedelta(hours=2))
    report4 = DelayReport.objects.create(order=orders[4], delay=timedelta(hours=3))


    response = client.get(reverse('delay-report'))
    data = response.data

    vendor1_expected_delay = timedelta(hours=10)
    vendor2_expected_delay = timedelta(hours=5)


    assert response.status_code == status.HTTP_200_OK

    assert len(data) == 2
    assert data[0]['vendor_id'] == orders[0].vendor.id
    assert data[0]['total_delay'] == str(vendor1_expected_delay)

    assert data[1]['vendor_id'] == orders[-1].vendor.id
    assert data[1]['total_delay'] == '0' + str(timedelta(hours=5))


