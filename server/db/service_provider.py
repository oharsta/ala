from uuid import uuid4

from flask import current_app


class ServiceProvider:

    @staticmethod
    def find_or_insert_by_entity_id(entity_id):
        service_providers = current_app.mongo.db.service_providers
        sp = service_providers.find_one({"entity_id": entity_id})
        if not sp:
            service_providers.insert_one({"_id": str(uuid4()), "entity_id": entity_id})
            sp = service_providers.find_one({"entity_id": entity_id})
        return sp
