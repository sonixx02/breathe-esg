from pathlib import Path

from django.contrib.auth import authenticate
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.http import JsonResponse

@ensure_csrf_cookie
def csrf_init(request):
    return JsonResponse({'csrfToken': get_token(request)})


def get_acting_user(request):
    from django.contrib.auth.models import User
    user = request.user
    if user and user.is_authenticated:
        return user
    acting_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not acting_user:
        acting_user, _ = User.objects.get_or_create(username="analyst", defaults={"is_staff": True})
    return acting_user


from .models import ActivityLog, EmissionRecord, IngestionBatch, RawIngestionRow
from .serializers import (
    ActivityLogSerializer,
    EmissionRecordSerializer,
    IngestionBatchSerializer,
    RawIngestionRowSerializer,
    UserSerializer,
)
from .services import get_default_client, load_demo_file, process_csv_upload


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    user = get_acting_user(request)
    if user and user.is_authenticated:
        Token.objects.filter(user=user).delete()
    return Response({"detail": "Logged out."})


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def upload_view(request):
    source_type = (request.data.get("source_type") or "").upper()
    upload = request.FILES.get("file")

    if source_type not in ("SAP", "UTILITY", "TRAVEL"):
        return Response(
            {"detail": "source_type must be SAP, UTILITY, or TRAVEL."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not upload:
        return Response(
            {"detail": "A CSV file is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = get_acting_user(request)
    batch = process_csv_upload(get_default_client(), user, source_type, upload.name, upload)
    return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def demo_load_view(request):
    source_type = (request.data.get("source_type") or "ALL").upper()
    
    # Check if demo data was already loaded to prevent duplicate confusion
    prefix = "demo_sample_"
    if source_type != "ALL":
        prefix += source_type.lower()
        
    if IngestionBatch.objects.filter(file_name__startswith=prefix).exists():
        return Response(
            {"detail": f"Demo data for {source_type} has already been loaded! Refresh the page or check the dashboard."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if source_type == "ALL":
        source_types = ["SAP", "UTILITY", "TRAVEL"]
    elif source_type in ("SAP", "UTILITY", "TRAVEL"):
        source_types = [source_type]
    else:
        return Response(
            {"detail": "source_type must be SAP, UTILITY, TRAVEL, or ALL."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = get_acting_user(request)
    batches = [load_demo_file(get_default_client(), user, value) for value in source_types]
    return Response({"batches": IngestionBatchSerializer(batches, many=True).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def demo_clear_view(request):
    client = get_default_client()
    ActivityLog.objects.filter(client=client).delete()
    EmissionRecord.objects.filter(client=client).delete()
    RawIngestionRow.objects.filter(client=client).delete()
    IngestionBatch.objects.filter(client=client).delete()
    return Response({"detail": "All ingested batches and records cleared successfully."})



@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_summary_view(request):
    client = get_default_client()
    records = EmissionRecord.objects.filter(client=client)
    status_counts = {item["status"]: item["count"] for item in records.values("status").annotate(count=Count("id"))}
    return Response(
        {
            "client": {"id": client.id, "name": client.name},
            "batches": IngestionBatch.objects.filter(client=client).count(),
            "records": records.count(),
            "raw_failures": RawIngestionRow.objects.filter(client=client, parse_status="FAILED").count(),
            "status_counts": status_counts,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def batch_list_view(request):
    batches = (
        IngestionBatch.objects.filter(client=get_default_client())
        .select_related("uploaded_by")
        .order_by("-uploaded_at")
    )
    return Response(IngestionBatchSerializer(batches, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def record_list_view(request):
    records = (
        EmissionRecord.objects.filter(client=get_default_client())
        .select_related("batch", "raw_row", "approved_by")
        .order_by("-updated_at")
    )

    record_status = request.query_params.get("status")
    source_type = request.query_params.get("source_type")
    if record_status:
        records = records.filter(status=record_status.upper())
    if source_type:
        records = records.filter(source_type=source_type.upper())

    return Response(EmissionRecordSerializer(records, many=True).data)


@api_view(["PATCH"])
@permission_classes([AllowAny])
def record_detail_view(request, record_id):
    try:
        record = EmissionRecord.objects.select_related("batch", "raw_row", "approved_by").get(
            id=record_id,
            client=get_default_client(),
        )
    except EmissionRecord.DoesNotExist:
        return Response({"detail": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

    if record.status == "LOCKED":
        return Response(
            {"detail": "Locked records cannot be edited."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    editable_fields = [
        "activity_category",
        "normalized_value",
        "normalized_unit",
        "location_name",
        "review_comment",
    ]
    old_values = {field: str(getattr(record, field)) for field in editable_fields if field in request.data}

    serializer = EmissionRecordSerializer(record, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save(is_manually_edited=True)

    record.refresh_from_db()
    new_values = {field: str(getattr(record, field)) for field in old_values}
    user = get_acting_user(request)
    ActivityLog.objects.create(
        client=record.client,
        record=record,
        action_type="EDITED",
        old_values=old_values,
        new_values=new_values,
        comment=request.data.get("review_comment", ""),
        acted_by=user,
    )
    return Response(EmissionRecordSerializer(record).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def approve_record_view(request, record_id):
    try:
        record = EmissionRecord.objects.get(id=record_id, client=get_default_client())
    except EmissionRecord.DoesNotExist:
        return Response({"detail": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

    if record.status == "LOCKED":
        return Response(
            {"detail": "Locked records are already final."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_status = record.status
    user = get_acting_user(request)
    record.status = "APPROVED"
    record.review_comment = request.data.get("review_comment", record.review_comment)
    record.approved_by = user
    record.approved_at = timezone.now()
    record.save(update_fields=["status", "review_comment", "approved_by", "approved_at", "updated_at"])

    ActivityLog.objects.create(
        client=record.client,
        record=record,
        action_type="APPROVED",
        old_values={"status": old_status},
        new_values={"status": "APPROVED"},
        comment=record.review_comment,
        acted_by=user,
    )
    return Response(EmissionRecordSerializer(record).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def lock_record_view(request, record_id):
    try:
        record = EmissionRecord.objects.get(id=record_id, client=get_default_client())
    except EmissionRecord.DoesNotExist:
        return Response({"detail": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

    if record.status != "APPROVED":
        return Response(
            {"detail": "Only approved records can be locked."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_status = record.status
    record.status = "LOCKED"
    record.locked_at = timezone.now()
    record.save(update_fields=["status", "locked_at", "updated_at"])

    user = get_acting_user(request)
    ActivityLog.objects.create(
        client=record.client,
        record=record,
        action_type="LOCKED",
        old_values={"status": old_status},
        new_values={"status": "LOCKED"},
        comment="Locked individually by analyst",
        acted_by=user,
    )
    return Response(EmissionRecordSerializer(record).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def lock_batch_view(request, batch_id):
    try:
        batch = IngestionBatch.objects.get(id=batch_id, client=get_default_client())
    except IngestionBatch.DoesNotExist:
        return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)

    records = EmissionRecord.objects.filter(batch=batch, status="APPROVED")
    locked_count = 0
    for record in records:
        record.status = "LOCKED"
        record.locked_at = timezone.now()
        record.save(update_fields=["status", "locked_at", "updated_at"])
        locked_count += 1
        user = get_acting_user(request)
        ActivityLog.objects.create(
            client=record.client,
            record=record,
            action_type="LOCKED",
            old_values={"status": "APPROVED"},
            new_values={"status": "LOCKED"},
            comment=f"Locked with batch {batch.id}",
            acted_by=user,
        )

    return Response({"batch_id": batch.id, "locked_records": locked_count})


@api_view(["GET"])
@permission_classes([AllowAny])
def record_activity_view(request, record_id):
    logs = ActivityLog.objects.filter(
        client=get_default_client(),
        record_id=record_id,
    ).select_related("acted_by").order_by("-acted_at")
    return Response(ActivityLogSerializer(logs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def raw_row_list_view(request):
    rows = (
        RawIngestionRow.objects.filter(client=get_default_client())
        .select_related("batch")
        .order_by("-created_at")
    )
    parse_status = request.query_params.get("parse_status")
    if parse_status:
        rows = rows.filter(parse_status=parse_status.upper())
    return Response(RawIngestionRowSerializer(rows, many=True).data)


def frontend_app(request):
    index_path = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"
    if index_path.exists():
        return HttpResponse(index_path.read_text(encoding="utf-8"))
    return HttpResponse(
        "Frontend build not found. Run npm install and npm run build inside the frontend folder.",
        content_type="text/plain",
    )
