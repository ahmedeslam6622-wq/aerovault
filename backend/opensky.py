"""
OpenSky Network Integration
============================
Fetches real-time EgyptAir (MS) aircraft positions from OpenSky Network.
Completely free, no API key needed, no rate limits for anonymous use.

We merge:
  - REAL from OpenSky: callsign, lat/lon, altitude, speed, on_ground status
  - FAKE (ours):       gate, terminal, delay, passenger counts, crew, maintenance

This gives a hybrid that looks live but always has complete operational data.
"""

import httpx
import asyncio
from typing import Optional

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# EgyptAir ICAO callsign prefix is "MSR"
EGYPTAIR_CALLSIGN_PREFIX = "MSR"

# CAI airport bounding box (lat_min, lat_max, lon_min, lon_max)
CAI_BBOX = (29.8, 30.3, 31.2, 31.7)


async def fetch_egyptair_positions() -> dict:
    """
    Fetch all EgyptAir flights currently tracked by OpenSky.
    Returns dict keyed by callsign (e.g. "MSR986") -> position data.
    Times out gracefully — if OpenSky is down, returns empty dict.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(OPENSKY_URL, params={
                "lamin": 20.0,   # South of Egypt
                "lamax": 45.0,   # North (covers Europe/Middle East routes)
                "lomin": 20.0,   # West
                "lomax": 55.0,   # East (covers Gulf)
            })
            if resp.status_code != 200:
                return {}

            data = resp.json()
            states = data.get("states") or []

            result = {}
            for s in states:
                # OpenSky state vector format:
                # [icao24, callsign, origin_country, time_position, last_contact,
                #  longitude, latitude, baro_altitude, on_ground, velocity,
                #  true_track, vertical_rate, sensors, geo_altitude, squawk,
                #  spi, position_source]
                if not s or len(s) < 10:
                    continue
                callsign = (s[1] or '').strip()
                if not callsign.startswith(EGYPTAIR_CALLSIGN_PREFIX):
                    continue

                longitude   = s[5]
                latitude    = s[6]
                altitude_m  = s[7]   # barometric altitude in meters
                on_ground   = s[8]
                speed_ms    = s[9]   # velocity in m/s

                result[callsign] = {
                    "callsign":    callsign,
                    "latitude":    latitude,
                    "longitude":   longitude,
                    "altitude_ft": int(altitude_m * 3.28084) if altitude_m else None,
                    "speed_kts":   int(speed_ms * 1.94384)  if speed_ms  else None,
                    "on_ground":   on_ground,
                    "live":        True,
                }
            return result

    except Exception:
        return {}


def merge_flight_with_live(flight_dict: dict, live_positions: dict) -> dict:
    """
    Merge a flight dict with live OpenSky data if available.
    Callsign in our DB looks like "MSR986"; OpenSky uses same format.
    """
    callsign = flight_dict.get("callsign", "")
    live = live_positions.get(callsign)

    if live:
        # Override position data with live data
        flight_dict["latitude"]    = live["latitude"]
        flight_dict["longitude"]   = live["longitude"]
        flight_dict["altitude_ft"] = live["altitude_ft"]
        flight_dict["speed_kts"]   = live["speed_kts"]
        flight_dict["live_tracking"] = True

        # Update status based on live ground status
        if live["on_ground"] and flight_dict["status"] in ("en_route", "approaching", "departed"):
            flight_dict["status"] = "on_ground"
        elif not live["on_ground"] and flight_dict["status"] in ("scheduled", "boarding"):
            flight_dict["status"] = "departed"
    else:
        flight_dict["live_tracking"] = False

    return flight_dict
