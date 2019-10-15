from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        users = self.db.users
        users.create_index("eduperson_principal_name", name="users_unique_eduperson_principal_name", unique=True)

    def downgrade(self):
        pass
