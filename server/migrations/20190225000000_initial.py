from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        users = self.db.users
        users.create_index("eduperson_principal_name", name="users_unique_eduperson_principal_name", unique=True)

        service_providers = self.db.service_providers
        service_providers.create_index("entity_id", name="service_providers_unique_entity_id", unique=True)

    def downgrade(self):
        pass
