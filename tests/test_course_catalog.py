from src.app.course_catalog import CourseCatalogService, CourseRecord, build_catalog, humanize_metadata_value
from src.app.static_courses import STATIC_COURSE_RECORDS


def test_humanize_metadata_value():
    assert (
        humanize_metadata_value("MachineLearning_for_Vision_and_Multimedia")
        == "Machine Learning For Vision And Multimedia"
    )
    assert humanize_metadata_value("Applicazioni Web I") == "Applicazioni Web I"
    assert humanize_metadata_value("API Programming") == "API Programming"


def test_build_catalog_groups_by_degree_and_year():
    catalog = build_catalog(
        [
            CourseRecord("Magistrale", "Primo Anno", "Data Science"),
            CourseRecord("Magistrale", "Primo Anno", "Applicazioni Web I"),
            CourseRecord("Triennale", "Secondo Anno", "Algoritmi_e_Programmazione"),
        ],
        "static",
    )

    assert catalog.source == "static"
    assert len(catalog.degrees) == 2
    magistrale = next(item for item in catalog.degrees if item.value == "Magistrale")
    assert magistrale.years[0].value == "Primo Anno"
    assert [course.value for course in magistrale.years[0].courses] == [
        "Applicazioni Web I",
        "Data Science",
    ]


def test_static_catalog_is_available_without_filesystem():
    service = CourseCatalogService(
        client=object(),
        collection_name="uni_docs",
    )
    catalog = service.get_catalog()

    assert catalog.source == "static"
    assert len(STATIC_COURSE_RECORDS) == 37
    assert all("semestre" not in item["course"].lower() for item in STATIC_COURSE_RECORDS)
    magistrale = next(degree for degree in catalog.degrees if degree.value == "Magistrale")
    secondo_anno = next(year for year in magistrale.years if year.value == "Secondo Anno")
    assert any(course.value == "MachineLearning_for_Vision_and_Multimedia" for course in secondo_anno.courses)
