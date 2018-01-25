from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    # url(r'^match/', views.match),
    # url(r'^([0-9]+)/$', views.detail),
]
