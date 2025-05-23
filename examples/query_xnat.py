import logging

from dicomsync.core import Domain
from dicomsync.xnat import XNATProjectPreArchive

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("PIL").level = logging.WARNING
logging.getLogger("urllib3").level = logging.INFO
logger = logging.getLogger()

place = XNATProjectPreArchive(
    project_name="xnat_project_name", server="https:xnat_endpoint", user="username"
)

domain = Domain(places={"pre_archive": place})
studies = [x for x in domain.query_studies("pre_archive:*")]

print(f"found {[str(x) for x in studies]}")
