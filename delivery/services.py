from datetime import datetime, timedelta
from enum import Enum
from typing import List

import requests
from django.db.models import Q, Sum
from pytz import timezone as tz
from rest_framework import status
from rest_framework.response import Response

from delivery.models import (Agent, DelayQueue, DelayReport, DelayStatus,
                             DeliveryStatus, Order, Trip)
from delivery.serializers import (DelayQueueReponseSerializer,
                                  DelayReportResponseSerializer)


class DelatyreationStatus(Enum):
    CREATED = 0
    NOT_CREATED = 1


def generate_response_from_serializer(serializer, status):
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)
    return Response(data=serializer.data, status=status)



class AnnounceDelayService:
    @staticmethod
    def announce(order_id):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not AnnounceDelayService._check_delivery_time_has_passed(order):
            return Response({'message': 'Delay time has not passed yet.'}, status=status.HTTP_412_PRECONDITION_FAILED)

        now = datetime.now().replace(tzinfo=tz('UTC'))
        delay = now - order.delivery_time

        try:
            report = DelayReport.objects.get(order=order)
            report.delay = delay
            report.save()
        except DelayReport.DoesNotExist:
            report = DelayReport.objects.create(order=order, delay=delay)

        trip: Trip = order.trip.select_related()

        if not trip or trip[0].status == DeliveryStatus.DELIVERED:
            if AnnounceDelayService._add_delay_to_queue(report) == DelatyreationStatus.CREATED:
                return Response({'message': 'Order placed in report queue'}, status=status.HTTP_200_OK)
            return Response({'message': 'Order is in the queue already'}, status=status.HTTP_200_OK)


        # The API does not work! So, I add 30 minutes to delivery_time manually.
        update_delay_endpoint = 'https://run.mocky.io/v3/122c2796-5df4-461c-ab75-87c1192b17f7'
        res = requests.get(update_delay_endpoint)

        order.delivery_time += timedelta(minutes=30)
        order.save()
        return Response({'new_delivery_time': order.delivery_time}, status=status.HTTP_200_OK)


    @staticmethod
    def _check_delivery_time_has_passed(order: Order):
        now = datetime.now().replace(tzinfo=tz('UTC'))
        if now < order.delivery_time:
            return False
        return True

    @staticmethod
    def _add_delay_to_queue(report):
        delays = DelayQueue.objects.filter(report=report)

        if not delays:
            DelayQueue.objects.create(report=report)
            return DelatyreationStatus.CREATED

        # User can add delay again only if the previouse delays has resolved.
        try:
            DelayQueue.objects.get(~Q(status=DelayStatus.RESOLVED), report=report)
            return DelatyreationStatus.NOT_CREATED

        except DelayQueue.DoesNotExist:
            DelayQueue.objects.create(report=report)
            return DelatyreationStatus.CREATED


class DelayQueueService:
    @staticmethod
    def give_delay_queue_to_agent(agent_id):
        try:
            agent = Agent.objects.get(pk=agent_id)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent nou found'}, status=status.HTTP_404_NOT_FOUND)

        delays: List[DelayQueue] = DelayQueue.objects.all().order_by('created_at').select_related()
        assining_delays = []

        for delay in delays:
            if delay.status == DelayStatus.UNASSIGNED:
                delay.agent = agent
                delay.status = DelayStatus.ASSIGNED
                delay.save()
                assining_delays.append(delay)

        serializer = DelayQueueReponseSerializer(assining_delays, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class DelayReportService:
    @staticmethod
    def get_delays_per_vendor():
        now = datetime.now().replace(tzinfo=tz('UTC'))
        last_week = now - timedelta(days=7)

        delays = DelayReport.objects.filter(Q(created_at__gte=last_week)) \
            .values('order__vendor') \
            .annotate(total_delay=Sum('delay')) \
            .order_by('-total_delay')

        for delay in delays:
            delay['vendor_id'] = delay.pop('order__vendor')

        serializer = DelayReportResponseSerializer(delays, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
