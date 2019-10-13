from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        users = self.db.users
        users.create_index("sub", name="users_unique_sub", unique=True)

    def downgrade(self):
        pass
