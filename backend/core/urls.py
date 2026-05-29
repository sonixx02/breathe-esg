from django.urls import path

from . import views

urlpatterns = [
    path("uploads/", views.upload_view),
    path("demo/load/", views.demo_load_view),
    path("demo/clear/", views.demo_clear_view),
    path("dashboard/summary/", views.dashboard_summary_view),
    path("batches/", views.batch_list_view),
    path("records/", views.record_list_view),
    path("records/<int:record_id>/", views.record_detail_view),
    path("records/<int:record_id>/approve/", views.approve_record_view),
    path("records/<int:record_id>/lock/", views.lock_record_view),
    path("records/<int:record_id>/activity/", views.record_activity_view),
    path("batches/<int:batch_id>/lock/", views.lock_batch_view),
    path("raw-rows/", views.raw_row_list_view),
]
