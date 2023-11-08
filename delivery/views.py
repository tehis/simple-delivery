from queue import Queue

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from delivery.serializers import (AnnounceOrderDelaySerializer,
                                  DelayQueueSerializer)
from delivery.services import (AnnounceDelayService, DelayQueueService,
                               DelayReportService)


class AnnounceOrderDelay(APIView):
    def post(self, request):
        serializer = AnnounceOrderDelaySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        order_id = serializer.validated_data.get('order_id')
        return AnnounceDelayService.announce(order_id)


class DelayQueue(APIView):
    def get(self, request):
        serializer = DelayQueueSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        agent_id = serializer.validated_data.get('agent_id')
        return DelayQueueService.give_delay_queue_to_agent(agent_id=agent_id)


class DelayReport(APIView):
    def get(self, request):
        return DelayReportService.get_delays_per_vendor()
