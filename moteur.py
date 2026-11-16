"""Démonstrateur hors ligne GreenMove. Coordonnées géographiques en degrés."""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def number(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("mesure non finie")
    return x


def xy(row):
    x, y = number(row["lon"]), number(row["lat"])
    if abs(x) > 180 or abs(y) > 90:
        raise ValueError("coordonnées hors domaine")
    return x, y


def contains(point, polygon, bounds):
    x, y = point
    west, south, east, north = bounds
    if not (west <= x <= east and south <= y <= north):
        return False
    inside = False
    for (a, b), (c, d) in zip(polygon, polygon[1:]):
        cross = (c-a)*(y-b) - (d-b)*(x-a)
        if abs(cross) < 1e-12 and min(a,c) <= x <= max(a,c) and min(b,d) <= y <= max(b,d):
            return True  # Frontière incluse
        if (b > y) != (d > y) and x < a + (y-b)*(c-a)/(d-b):
            inside = not inside
    return inside


def geo(folder):
    polygon = [xy(p) for p in json.loads((folder/'lyon_polygon.json').read_text())]
    if len(set(polygon)) < 3:
        raise ValueError("polygone incomplet")
    if polygon[0] != polygon[-1]:
        polygon.append(polygon[0])
    xs, ys = zip(*polygon)
    bounds = min(xs), min(ys), max(xs), max(ys)
    previous = False
    for index, row in enumerate(json.loads((folder/'truck_gps.json').read_text()), 1):
        try:
            current = contains(xy(row), polygon, bounds)
            stamp = row["timestamp"]
        except (KeyError, ValueError, TypeError) as err:
            print(f"[GPS ignoré] point {index} : {err}")
            continue
        print(stamp, "IN" if current else "OUT",
              "[ALERT ZFE]" if current and not previous else "", flush=True)
        previous = current


def safety(folder, output, threshold):
    events = []
    valid = skipped = 0
    active = False
    day = None
    with (folder/'accelerometer_data.csv').open(newline="") as source:
        reader = csv.DictReader(source)
        if not {"timestamp", "acc_y", "acc_x", "acc_z"}.issubset(reader.fieldnames or []):
            raise ValueError("colonnes CSV manquantes")
        for row in reader:
            try:
                stamp = int(row["timestamp"])
                date = datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()
                _, y, _ = [number(row[k]) for k in ("acc_x","acc_y","acc_z")]
            except (TypeError, ValueError, OverflowError, OSError) as err:
                skipped += 1
                print(f"[CSV ignoré] ligne {reader.line_num} : {err}")
                continue
            if day is not None and date != day:
                raise ValueError("fournir un fichier par journée UTC")
            day = date
            valid += 1
            if y < -threshold:
                if not active:
                    events.append({"timestamp":stamp, "min_y_m_s2":y})
                    print("[FREINAGE]", stamp, y, "m/s²")
                else:
                    events[-1]["min_y_m_s2"] = min(events[-1]["min_y_m_s2"], y)
                active = True
            elif y >= -threshold * 0.8:
                active = False
    if not valid:
        raise ValueError("aucune mesure valide")
    result = dict(date_utc=day, seuil_m_s2=threshold, mesures=valid, ignorees=skipped,
                  freinages=len(events), evenements=events,
                  score_demo=max(0,100-10*len(events)))
    temp = output.with_suffix(output.suffix+'.tmp')
    temp.write_text(json.dumps(result, indent=2)+'\n')
    temp.replace(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path(__file__).parent/"data")
    parser.add_argument("--sortie", type=Path, default=Path("daily_score.json"))
    parser.add_argument("--seuil", type=number, default=2.5)
    args = parser.parse_args()
    if args.seuil <= 0:
        parser.error("le seuil doit être positif")
    failed = False
    for label, action in [("Geo", lambda: geo(args.data)),
                          ("Safety", lambda: safety(args.data,args.sortie,args.seuil))]:
        try:
            action()
        except (OSError, ValueError, KeyError, TypeError, csv.Error) as err:
            print(f"[{label} indisponible] {err}")
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
