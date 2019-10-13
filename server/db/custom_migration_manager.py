from mongodb_migrations.cli import MigrationManager
from mongodb_migrations.config import Configuration


class CustomConfiguration(Configuration):

    def __init__(self, migrations_path, ini_file):
        self.config_file = f"{migrations_path}/{ini_file}"
        self._from_ini()
        self.mongo_migrations_path = migrations_path


class CustomMigrationManager(MigrationManager):

    def __init__(self, migrations_path, ini_file):
        self.config = CustomConfiguration(migrations_path, ini_file)
