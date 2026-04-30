from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class GPXtrkpt:
    latitude: float
    longitude: float
    time: datetime


@dataclass
class GPXtrkseg:
    points: List[Optional[GPXtrkpt]]


@dataclass
class GPXtrk:
    name: str
    segments: List[Optional[GPXtrkseg]]


class GPXcalculator:

    @staticmethod
    def calculate_distance_traveled(track: Optional[GPXtrk]) -> float:
        # Undefined structure
        if track is None:
            return -1.0

        segments = track.segments
        if segments is None or len(segments) == 0:
            return -1.0

        total = 0.0

        for seg in segments:
            if seg is None:
                continue

            pts = seg.points
            if pts is None or len(pts) < 2:
                continue

            for i in range(len(pts) - 1):
                p1 = pts[i]
                p2 = pts[i + 1]

                if p1 is None or p2 is None:
                    continue

                lat1, lon1 = p1.latitude, p1.longitude
                lat2, lon2 = p2.latitude, p2.longitude

                # Enforce admissible geographic bounds
                if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
                    continue
                if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
                    continue

                # Manhattan-style distance
                total += abs(lat2 - lat1) + abs(lon2 - lon1)

        return total
