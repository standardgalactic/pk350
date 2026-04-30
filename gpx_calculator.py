#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import sys


# --- DATA STRUCTURES ---

@dataclass
class GPXtrkpt:
    latitude: float
    longitude: float
    time: Optional[datetime]


@dataclass
class GPXtrkseg:
    points: List[Optional[GPXtrkpt]]


@dataclass
class GPXtrk:
    name: str
    segments: List[Optional[GPXtrkseg]]


# --- CALCULATOR (UNCHANGED SEMANTICS) ---

class GPXcalculator:

    @staticmethod
    def is_valid_point(p: GPXtrkpt) -> bool:
        return (
            p is not None and
            -90 <= p.latitude <= 90 and
            -180 <= p.longitude <= 180
        )

    @staticmethod
    def segment_distance(seg: Optional[GPXtrkseg]) -> float:
        if seg is None or seg.points is None or len(seg.points) < 2:
            return 0.0

        total = 0.0
        pts = seg.points

        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i + 1]

            if not (GPXcalculator.is_valid_point(p1) and
                    GPXcalculator.is_valid_point(p2)):
                continue

            total += abs(p2.latitude - p1.latitude) + \
                     abs(p2.longitude - p1.longitude)

        return total

    @staticmethod
    def calculate_distance_traveled(track: Optional[GPXtrk]) -> float:
        if track is None:
            return -1.0

        if track.segments is None or len(track.segments) == 0:
            return -1.0

        total = 0.0

        for seg in track.segments:
            total += GPXcalculator.segment_distance(seg)

        return total


# --- GPX PARSER ---

def parse_time(t):
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except:
        return None


def parse_gpx(file_path: str) -> Optional[GPXtrk]:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except:
        return None

    # Handle namespace if present
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    tracks = root.findall(f"{ns}trk")
    if not tracks:
        return GPXtrk("Empty", [])

    segments = []

    for trk in tracks:
        for seg in trk.findall(f"{ns}trkseg"):
            points = []

            for pt in seg.findall(f"{ns}trkpt"):
                try:
                    lat = float(pt.attrib.get("lat"))
                    lon = float(pt.attrib.get("lon"))
                except:
                    points.append(None)
                    continue

                time_elem = pt.find(f"{ns}time")
                time_val = parse_time(time_elem.text) if time_elem is not None else None

                points.append(GPXtrkpt(lat, lon, time_val))

            segments.append(GPXtrkseg(points))

    return GPXtrk("Parsed Track", segments)


# --- CLI ENTRY POINT ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python gpx_calc.py <file.gpx>")
        return

    file_path = sys.argv[1]
    track = parse_gpx(file_path)

    distance = GPXcalculator.calculate_distance_traveled(track)

    print(f"Distance (constraint-aware): {distance}")


if __name__ == "__main__":
    main()
