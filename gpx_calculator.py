#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import math
import sys


@dataclass
class GPXtrkpt:
    latitude: float
    longitude: float
    time: Optional[datetime] = None


@dataclass
class GPXtrkseg:
    points: List[Optional[GPXtrkpt]]


@dataclass
class GPXtrk:
    name: str
    segments: List[Optional[GPXtrkseg]]


class GPXcalculator:
    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def is_valid_point(p: Optional[GPXtrkpt]) -> bool:
        return (
            p is not None
            and -90 <= p.latitude <= 90
            and -180 <= p.longitude <= 180
        )

    @staticmethod
    def constraint_step_distance(p1: GPXtrkpt, p2: GPXtrkpt) -> float:
        return abs(p2.latitude - p1.latitude) + abs(p2.longitude - p1.longitude)

    @staticmethod
    def geodesic_step_distance(p1: GPXtrkpt, p2: GPXtrkpt) -> float:
        lat1 = math.radians(p1.latitude)
        lon1 = math.radians(p1.longitude)
        lat2 = math.radians(p2.latitude)
        lon2 = math.radians(p2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return GPXcalculator.EARTH_RADIUS_KM * c

    @staticmethod
    def segment_constraint_distance(seg: Optional[GPXtrkseg]) -> float:
        if seg is None or seg.points is None or len(seg.points) < 2:
            return 0.0

        total = 0.0

        for i in range(len(seg.points) - 1):
            p1 = seg.points[i]
            p2 = seg.points[i + 1]

            if not (
                GPXcalculator.is_valid_point(p1)
                and GPXcalculator.is_valid_point(p2)
            ):
                continue

            total += GPXcalculator.constraint_step_distance(p1, p2)

        return total

    @staticmethod
    def segment_geodesic_distance(seg: Optional[GPXtrkseg]) -> float:
        if seg is None or seg.points is None or len(seg.points) < 2:
            return 0.0

        total = 0.0

        for i in range(len(seg.points) - 1):
            p1 = seg.points[i]
            p2 = seg.points[i + 1]

            if not (
                GPXcalculator.is_valid_point(p1)
                and GPXcalculator.is_valid_point(p2)
            ):
                continue

            total += GPXcalculator.geodesic_step_distance(p1, p2)

        return total

    @staticmethod
    def calculate_distance_traveled(track: Optional[GPXtrk]) -> float:
        if track is None:
            return -1.0

        if track.segments is None or len(track.segments) == 0:
            return -1.0

        total = 0.0

        for seg in track.segments:
            total += GPXcalculator.segment_constraint_distance(seg)

        return total

    @staticmethod
    def calculate_geodesic_distance(track: Optional[GPXtrk]) -> float:
        if track is None:
            return -1.0

        if track.segments is None or len(track.segments) == 0:
            return -1.0

        total = 0.0

        for seg in track.segments:
            total += GPXcalculator.segment_geodesic_distance(seg)

        return total

    @staticmethod
    def calculate_residuals(track: Optional[GPXtrk]) -> List[dict]:
        residuals = []

        if track is None or track.segments is None:
            return residuals

        for seg_index, seg in enumerate(track.segments):
            if seg is None or seg.points is None or len(seg.points) < 2:
                continue

            for point_index in range(len(seg.points) - 1):
                p1 = seg.points[point_index]
                p2 = seg.points[point_index + 1]

                if not (
                    GPXcalculator.is_valid_point(p1)
                    and GPXcalculator.is_valid_point(p2)
                ):
                    continue

                constraint_distance = GPXcalculator.constraint_step_distance(p1, p2)
                geodesic_distance = GPXcalculator.geodesic_step_distance(p1, p2)

                residual = geodesic_distance - constraint_distance

                ratio = None
                if constraint_distance != 0:
                    ratio = geodesic_distance / constraint_distance

                residuals.append(
                    {
                        "segment": seg_index,
                        "step": point_index,
                        "from": (p1.latitude, p1.longitude),
                        "to": (p2.latitude, p2.longitude),
                        "constraint_distance": constraint_distance,
                        "geodesic_distance_km": geodesic_distance,
                        "residual": residual,
                        "ratio": ratio,
                    }
                )

        return residuals

    @staticmethod
    def summarize(track: Optional[GPXtrk]) -> dict:
        constraint_distance = GPXcalculator.calculate_distance_traveled(track)
        geodesic_distance = GPXcalculator.calculate_geodesic_distance(track)

        residuals = GPXcalculator.calculate_residuals(track)

        valid_steps = len(residuals)

        total_residual = 0.0
        max_residual = None
        max_ratio = None

        if residuals:
            total_residual = sum(r["residual"] for r in residuals)
            max_residual = max(residuals, key=lambda r: abs(r["residual"]))
            ratio_candidates = [r for r in residuals if r["ratio"] is not None]
            if ratio_candidates:
                max_ratio = max(ratio_candidates, key=lambda r: abs(r["ratio"]))

        return {
            "constraint_distance": constraint_distance,
            "geodesic_distance_km": geodesic_distance,
            "valid_steps": valid_steps,
            "total_residual": total_residual,
            "max_residual_step": max_residual,
            "max_ratio_step": max_ratio,
            "residuals": residuals,
        }


def parse_time(text: Optional[str]) -> Optional[datetime]:
    if text is None:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def parse_gpx(file_path: str) -> Optional[GPXtrk]:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception:
        return None

    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"

    tracks = root.findall(f"{namespace}trk")

    if not tracks:
        return GPXtrk("Empty", [])

    all_segments = []
    track_name = "Parsed Track"

    first_name = tracks[0].find(f"{namespace}name")
    if first_name is not None and first_name.text:
        track_name = first_name.text.strip()

    for trk in tracks:
        for seg in trk.findall(f"{namespace}trkseg"):
            points = []

            for pt in seg.findall(f"{namespace}trkpt"):
                try:
                    lat = float(pt.attrib.get("lat"))
                    lon = float(pt.attrib.get("lon"))
                except Exception:
                    points.append(None)
                    continue

                time_elem = pt.find(f"{namespace}time")
                time_value = parse_time(time_elem.text) if time_elem is not None else None

                points.append(GPXtrkpt(lat, lon, time_value))

            all_segments.append(GPXtrkseg(points))

    return GPXtrk(track_name, all_segments)


def print_summary(summary: dict) -> None:
    print("\n--- GPX Distance Report ---\n")

    print(f"Constraint distance: {summary['constraint_distance']}")
    print(f"Geodesic distance:   {summary['geodesic_distance_km']} km")
    print(f"Valid steps:         {summary['valid_steps']}")
    print(f"Total residual:      {summary['total_residual']}")

    if (
        summary["constraint_distance"] is not None
        and summary["constraint_distance"] > 0
        and summary["geodesic_distance_km"] >= 0
    ):
        ratio = summary["geodesic_distance_km"] / summary["constraint_distance"]
        print(f"Global ratio:        {ratio}")

    if summary["max_residual_step"] is not None:
        r = summary["max_residual_step"]
        print("\nLargest residual step:")
        print(f"  Segment:             {r['segment']}")
        print(f"  Step:                {r['step']}")
        print(f"  From:                {r['from']}")
        print(f"  To:                  {r['to']}")
        print(f"  Constraint distance: {r['constraint_distance']}")
        print(f"  Geodesic distance:   {r['geodesic_distance_km']} km")
        print(f"  Residual:            {r['residual']}")

    if summary["max_ratio_step"] is not None:
        r = summary["max_ratio_step"]
        print("\nLargest ratio step:")
        print(f"  Segment:             {r['segment']}")
        print(f"  Step:                {r['step']}")
        print(f"  From:                {r['from']}")
        print(f"  To:                  {r['to']}")
        print(f"  Ratio:               {r['ratio']}")


def write_residual_csv(summary: dict, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(
            "segment,step,from_lat,from_lon,to_lat,to_lon,"
            "constraint_distance,geodesic_distance_km,residual,ratio\n"
        )

        for r in summary["residuals"]:
            from_lat, from_lon = r["from"]
            to_lat, to_lon = r["to"]

            ratio = "" if r["ratio"] is None else r["ratio"]

            f.write(
                f"{r['segment']},{r['step']},"
                f"{from_lat},{from_lon},{to_lat},{to_lon},"
                f"{r['constraint_distance']},"
                f"{r['geodesic_distance_km']},"
                f"{r['residual']},"
                f"{ratio}\n"
            )


def example_track() -> GPXtrk:
    p1 = GPXtrkpt(-10.0, 0.0)
    p2 = GPXtrkpt(0.0, 0.0)
    p3 = GPXtrkpt(0.0, 10.0)

    seg1 = GPXtrkseg([p1, p2])
    seg2 = GPXtrkseg([p2, p3])

    return GPXtrk("Example Track", [seg1, seg2])


def main() -> None:
    if len(sys.argv) == 1:
        track = example_track()
        summary = GPXcalculator.summarize(track)
        print("No GPX file supplied. Running built-in example.")
        print_summary(summary)
        return

    file_path = sys.argv[1]
    track = parse_gpx(file_path)
    summary = GPXcalculator.summarize(track)

    print_summary(summary)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        write_residual_csv(summary, output_path)
        print(f"\nResidual CSV written to: {output_path}")


if __name__ == "__main__":
    main()
