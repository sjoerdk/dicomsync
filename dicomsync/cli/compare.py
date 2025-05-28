from typing import Iterable, List

import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import ForcedStudyQueryParameterType
from dicomsync.core import StudyType
from dicomsync.logs import get_module_logger
from dicomsync.references import StudyQuery
from jinja2.environment import Template

logger = get_module_logger("cli.compare")

compare_template = Template(
    """
# Only in '{{ study_query_a }}':
{% for item in only_in_a %}{{ item }}
{% endfor %}
# Both in '{{ study_query_a }}' and '{{ study_query_b }}':
{% for item in in_both %}{{ item }}
{% endfor %}
# Only in '{{ study_query_b }}':
{% for item in only_in_b %}{{ item }}
{% endfor %}
"""
)


@dicom_sync_command()
@click.argument("study_query_a", type=ForcedStudyQueryParameterType())
@click.argument("study_query_b", type=ForcedStudyQueryParameterType())
def compare(
    context: DicomSyncContext, study_query_a: StudyQuery, study_query_b: StudyQuery
):
    """Show which studies differ, which correspond between two places."""

    logger.debug(f"comparing '{study_query_a}' and '{study_query_b}'.")
    # place can be a query or just a place name
    # get current places
    domain = context.get_domain()

    in_both, only_in_a, only_in_b = find_overlap(
        domain.query_studies(query=study_query_a),
        domain.query_studies(query=study_query_b),
    )

    click.echo(
        compare_template.render(
            study_query_a=study_query_a.query_string(),
            study_query_b=study_query_b.query_string(),
            only_in_a=(domain.get_study_uri(x) for x in only_in_a),
            only_in_b=(domain.get_study_uri(x) for x in only_in_b),
            in_both=in_both,
        )
    )


def find_overlap(studies_a: Iterable[StudyType], studies_b: Iterable[StudyType]):
    """Find the overlap between two sets of studies, based on keys"""
    studies_dict_a = {str(x.key()): x for x in studies_a}
    studies_dict_b = {str(x.key()): x for x in studies_b}
    only_in_a: List[StudyType] = [
        study for key, study in studies_dict_a.items() if key not in studies_dict_b
    ]
    only_in_b: List[StudyType] = [
        study for key, study in studies_dict_b.items() if key not in studies_dict_a
    ]
    in_both: List[str] = [key for key in studies_dict_a if key in studies_dict_b]
    return in_both, only_in_a, only_in_b
