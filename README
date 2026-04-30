# GPX Constraint-Aware Distance Calculator

A minimal implementation for computing distance over GPX tracks with strict handling of structure and coordinate validity.

## Overview

This project treats a GPX track as a constrained trajectory rather than a simple list of points. Distance is computed only from valid, admissible transitions between points. Invalid data does not break the system; it is explicitly handled and contributes nothing to the final result.

## Core Idea

Distance is accumulated across consecutive points only when:

- Both points are non-null
- Latitude is within [-90, 90]
- Longitude is within [-180, 180]

Otherwise, the transition is ignored.

## Return Semantics

- `-1.0` → Track is null or has no segments (undefined structure)
- `0.0` → Track exists but has no valid transitions
- `> 0.0` → Sum of valid point-to-point distances

## Distance Model

Distance is computed using simple coordinate differences:

|Δlatitude| + |Δlongitude|

This reflects a discrete, local movement model rather than spherical (geodesic) distance.

## Project Structure

- `GPXtrkpt` — Represents a single track point (latitude, longitude, timestamp)
- `GPXtrkseg` — A sequence of track points
- `GPXtrk` — A full track composed of segments
- `GPXcalculator` — Computes total distance traveled

## Testing

The test suite defines the full behavior of the system, including:

- Null track handling
- Empty segments
- Segments with insufficient points
- Null points
- Out-of-bounds coordinates

## Purpose

This project provides a clean, constraint-aware foundation for working with trajectory data where correctness depends on both structure and admissibility, not just numerical computation.
