"""Build the bundled prenoms_sexe.csv — the tool provisions its own data.

By default this DOWNLOADS the official INSEE national first-names file (sovereign
open data, Licence Ouverte / Etalab) and builds the prénom→sexe table in one
command, with no manual file handling:

    uv run python scripts/build_prenoms_sexe.py

Offline / test override: pass a local INSEE CSV with --insee. Swiss OFS coverage
is optional: add --ofs-f / --ofs-m (';' CSVs with columns prenom;nombre). See
src/crewai_custom_tools/tools/genealogy/data/README.md for provenance.
"""

from __future__ import annotations

import argparse
import csv
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from crewai_custom_tools.tools.genealogy.analysis.gender import normkey

# INSEE « Fichier des prénoms » — fichier national (France, 1900→2025), CSV ';',
# colonnes : sexe;prenom;periode;valeur;rang (sexe 1=M, 2=F). Licence Ouverte.
# Édition épinglée ; à bumper lors d'une nouvelle édition (le format est toléré
# des deux côtés par _read_insee).
INSEE_URL = "https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025-nat_csv.zip"
_UA = "genecrew-build/1.0 (open data INSEE)"

DEFAULT_OUT = (Path(__file__).resolve().parents[1]
               / "src/crewai_custom_tools/tools/genealogy/data/prenoms_sexe.csv")


def _add(table: dict[str, tuple[int, int]], key: str, n_f: int = 0, n_m: int = 0) -> None:
    f, m = table.get(key, (0, 0))
    table[key] = (f + n_f, m + n_m)


def download_insee(dest_dir: Path) -> Path:
    """Download the INSEE national zip and extract its CSV into dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "insee_nat.zip"
    req = urllib.request.Request(INSEE_URL, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=120) as resp, open(zip_path, "wb") as fh:
        fh.write(resp.read())
    with zipfile.ZipFile(zip_path) as zf:
        csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        zf.extract(csv_name, dest_dir)
    return dest_dir / csv_name


def _read_insee(path: str, table: dict[str, tuple[int, int]]) -> None:
    """Aggregate INSEE births by normalized first name × sex, across all years.

    Tolerant to both the 2025 header (prenom/valeur) and the older one
    (preusuel/nombre). sexe 1 = masculin → n_m, 2 = féminin → n_f.
    """
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            name = row.get("prenom") or row.get("preusuel") or ""
            key = normkey(name)
            if not key:
                continue
            count = int(row.get("valeur") or row.get("nombre") or 0)
            if row["sexe"] == "1":
                _add(table, key, n_m=count)
            elif row["sexe"] == "2":
                _add(table, key, n_f=count)


def _read_ofs(path: str, table: dict[str, tuple[int, int]], *, female: bool) -> None:
    """Optional Swiss OFS source: ';' CSV with columns prenom;nombre."""
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            key = normkey(row["prenom"])
            if not key:
                continue
            count = int(row["nombre"])
            if female:
                _add(table, key, n_f=count)
            else:
                _add(table, key, n_m=count)


def build(insee: str | None = None, ofs_f: str | None = None,
          ofs_m: str | None = None, out: str | Path = DEFAULT_OUT) -> Path:
    """Build the table. Downloads the INSEE file when `insee` is None; OFS optional."""
    table: dict[str, tuple[int, int]] = {}
    if insee is None:
        with tempfile.TemporaryDirectory() as tmp:
            _read_insee(str(download_insee(Path(tmp))), table)
    else:
        _read_insee(insee, table)
    if ofs_f:
        _read_ofs(ofs_f, table, female=True)
    if ofs_m:
        _read_ofs(ofs_m, table, female=False)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["prenom", "n_f", "n_m"])
        for key in sorted(table):
            n_f, n_m = table[key]
            writer.writerow([key, n_f, n_m])
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build prenoms_sexe.csv (télécharge l'INSEE par défaut ; OFS optionnel)")
    ap.add_argument("--insee", default=None,
                    help="CSV INSEE local (sinon téléchargé automatiquement)")
    ap.add_argument("--ofs-f", default=None, help="CSV OFS féminin optionnel (prenom;nombre)")
    ap.add_argument("--ofs-m", default=None, help="CSV OFS masculin optionnel (prenom;nombre)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help=f"sortie (défaut : {DEFAULT_OUT})")
    a = ap.parse_args()
    print(f"Écrit : {build(a.insee, a.ofs_f, a.ofs_m, a.out)}")


if __name__ == "__main__":
    main()
