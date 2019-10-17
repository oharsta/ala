from configparser import ConfigParser

from mongodb_migrations.cli import MigrationManager
from mongodb_migrations.config import Configuration


class CustomConfiguration(Configuration):

    def __init__(self, migrations_path, ini_file):
        self.config_file = f"{migrations_path}/{ini_file}"
        fp = open(self.config_file)
        self.ini_parser = ConfigParser()
        with fp:
            self.ini_parser.read_file(fp)
            self.mongo_url = self.ini_parser.get("mongo", "url", fallback=None)
            self.mongo_host = self.ini_parser.get("mongo", "host", fallback=None)
            self.mongo_port = self.ini_parser.getint("mongo", "port", fallback=None)
            self.mongo_database = self.ini_parser.get("mongo", "database", fallback=None)
            self.mongo_username = self.ini_parser.get("mongo", "username", fallback=None)
            self.mongo_password = self.ini_parser.get("mongo", "password", fallback=None)
            self.metastore = self.ini_parser.get("mongo", "metastore", fallback=None)
        self.mongo_migrations_path = migrations_path


class CustomMigrationManager(MigrationManager):

    def __init__(self, migrations_path, ini_file):
        self.config = CustomConfiguration(migrations_path, ini_file)
