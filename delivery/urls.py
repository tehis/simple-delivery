from django.urls import path

from delivery import views

urlpatterns = [
    path('annouce-delay/', views.AnnounceOrderDelay.as_view(), name='annouce-delay'),
    path('delay-queue/', views.DelayQueue.as_view(), name='delay-queue'),
    path('delay-report/', views.DelayReport.as_view(), name='delay-report'),
]