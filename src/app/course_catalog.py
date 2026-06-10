"""Course catalog loading and label normalization."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Iterable, Literal

from qdrant_client import QdrantClient

from src.app.schemas import CourseCatalogResponse, CourseOption, DegreeOption, YearOption
from src.app.static_courses import STATIC_COURSE_RECORDS


_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z])(?=[A-Z])")
_WORD_SEPARATORS = re.compile(r"[_\-.]+")


@dataclass(frozen=True)
class CourseRecord:
    degree: str
    year: str
    course: str


def humanize_metadata_value(value: str) -> str:
    cleaned = _WORD_SEPARATORS.sub(" ", value).strip()
    cleaned = _CAMEL_BOUNDARY.sub(" ", cleaned)
    words = []
    for word in cleaned.split():
        if word.isupper() and len(word) > 1:
            words.append(word)
        elif re.fullmatch(r"[IVX]+", word.upper()):
            words.append(word.upper())
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return " ".join(words) or value


def build_catalog(records: Iterable[CourseRecord], source: Literal["qdrant", "static", "empty"]) -> CourseCatalogResponse:
    degree_map: dict[str, dict[str, set[str]]] = {}
    for record in records:
        if not record.degree or not record.year or not record.course:
            continue
        if "unknown" in {record.degree.lower(), record.year.lower(), record.course.lower()}:
            continue
        degree_map.setdefault(record.degree, {}).setdefault(record.year, set()).add(record.course)

    degrees: list[DegreeOption] = []
    for degree in sorted(degree_map, key=humanize_metadata_value):
        years: list[YearOption] = []
        for year in sorted(degree_map[degree], key=humanize_metadata_value):
            courses = [
                CourseOption(
                    label=humanize_metadata_value(course),
                    value=course,
                    degree=degree,
                    year=year,
                )
                for course in sorted(degree_map[degree][year], key=humanize_metadata_value)
            ]
            years.append(
                YearOption(
                    label=humanize_metadata_value(year),
                    value=year,
                    courses=courses,
                )
            )
        degrees.append(
            DegreeOption(
                label=humanize_metadata_value(degree),
                value=degree,
                years=years,
            )
        )

    return CourseCatalogResponse(source=source if degrees else "empty", degrees=degrees)


class CourseCatalogService:
    def __init__(
        self,
        *,
        client: QdrantClient,
        collection_name: str,
        ttl_seconds: int = 300,
    ):
        self.client = client
        self.collection_name = collection_name
        self.ttl_seconds = ttl_seconds
        self._cached_at = 0.0
        self._cached_catalog: CourseCatalogResponse | None = None

    def get_catalog(self, *, refresh: bool = False) -> CourseCatalogResponse:
        now = time.monotonic()
        if (
            not refresh
            and self._cached_catalog is not None
            and now - self._cached_at < self.ttl_seconds
        ):
            return self._cached_catalog

        catalog = self._load_static() if not refresh else self._load_from_qdrant()
        if not catalog.degrees:
            catalog = self._load_static()

        self._cached_catalog = catalog
        self._cached_at = now
        return catalog

    def _load_static(self) -> CourseCatalogResponse:
        records = {
            CourseRecord(
                degree=item["degree"],
                year=item["year"],
                course=item["course"],
            )
            for item in STATIC_COURSE_RECORDS
        }
        return build_catalog(records, "static")

    def _load_from_qdrant(self) -> CourseCatalogResponse:
        records: set[CourseRecord] = set()
        try:
            offset = None
            while True:
                points, offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=256,
                    offset=offset,
                    with_payload=["degree_level", "year", "course"],
                    with_vectors=False,
                )
                for point in points:
                    payload = point.payload or {}
                    records.add(
                        CourseRecord(
                            degree=str(payload.get("degree_level") or ""),
                            year=str(payload.get("year") or ""),
                            course=str(payload.get("course") or ""),
                        )
                    )
                if offset is None:
                    break
        except Exception:
            return CourseCatalogResponse(source="empty", degrees=[])
        return build_catalog(records, "qdrant")
