from rest_framework import serializers

from delivery.models import DelayQueue


class AnnounceOrderDelaySerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class DelayQueueSerializer(serializers.Serializer):
    agent_id = serializers.IntegerField()


class DelayQueueReponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DelayQueue
        fields = '__all__'


class DelayReportResponseSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    total_delay = serializers.DurationField()
