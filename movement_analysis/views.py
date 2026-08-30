import math

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MovementSession, MovementTrack
from .serializers import MovementSessionSerializer, MovementTrackSerializer


def _get_session(user, session_id):
    try:
        return MovementSession.objects.get(pk=session_id, created_by=user)
    except MovementSession.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def sessions_list(request):
    if request.method == "GET":
        sessions = MovementSession.objects.filter(created_by=request.user)
        return Response(MovementSessionSerializer(sessions, many=True).data)

    serializer = MovementSessionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(created_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def session_detail(request, session_id):
    session = _get_session(request.user, session_id)
    if session is None:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(MovementSessionSerializer(session).data)

    if request.method == "PUT":
        serializer = MovementSessionSerializer(session, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    session.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Tracks
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_track(request, session_id):
    session = _get_session(request.user, session_id)
    if session is None:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = MovementTrackSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(session=session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def _analyse_samples(samples):
    """
    samples: list of [t, x, y] (z optional). Returns basic kinematic metrics.
    """
    pts = [s for s in samples if isinstance(s, (list, tuple)) and len(s) >= 3]
    if len(pts) < 2:
        return {
            "n_samples": len(pts),
            "duration_s": 0.0,
            "path_length": 0.0,
            "mean_speed": 0.0,
            "max_speed": 0.0,
        }

    path_length = 0.0
    max_speed = 0.0
    for (t0, x0, y0, *r0), (t1, x1, y1, *r1) in zip(pts, pts[1:]):
        z0 = r0[0] if r0 else 0.0
        z1 = r1[0] if r1 else 0.0
        d = math.dist((x0, y0, z0), (x1, y1, z1))
        path_length += d
        dt = t1 - t0
        if dt > 0:
            max_speed = max(max_speed, d / dt)

    duration = pts[-1][0] - pts[0][0]
    mean_speed = path_length / duration if duration > 0 else 0.0

    return {
        "n_samples": len(pts),
        "duration_s": round(duration, 4),
        "path_length": round(path_length, 4),
        "mean_speed": round(mean_speed, 4),
        "max_speed": round(max_speed, 4),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_analysis(request, session_id):
    session = _get_session(request.user, session_id)
    if session is None:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    results = {
        track.label: _analyse_samples(track.samples)
        for track in session.tracks.all()
    }
    return Response({"session_id": session.id, "tracks": results})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyse_samples(request):
    """Stateless analysis: POST {"samples": [[t, x, y], ...]} -> metrics."""
    samples = request.data.get("samples") or []
    return Response(_analyse_samples(samples))
