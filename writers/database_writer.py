import logging

from db import (
    insert_application,
    insert_clouds,
    insert_controller,
    insert_juju_data_v1,
    insert_machine,
    insert_model,
    insert_unit,
    populate_unreachable_model,
    setup_juju_temp_tables_v1,
)
from domain.models import ControllerInfo, Model


class DatabaseWriter:
    def __init__(self, db_manager, entry_id: int):
        self.dbm = db_manager
        self.entry_id = entry_id
        self.logger = logging.getLogger("DatabaseWriter")

    async def _ensure_transaction(self):
        if not self.dbm.transaction:
            await self.dbm.start_transaction()

    async def prepare_controller(self, controller: ControllerInfo):
        await self._ensure_transaction()
        await setup_juju_temp_tables_v1(self.dbm.db)
        await insert_clouds(self.dbm.db, self.entry_id, controller.clouds)
        await insert_controller(self.dbm.db, self.entry_id, controller)

    async def write_model(self, model: Model):
        await self._ensure_transaction()
        await insert_model(self.dbm.db, self.entry_id, model)

        instance_ids = {}
        for machine in sorted(model.machines.values(), key=lambda m: m.ordinal):
            machine_id = await insert_machine(self.dbm.db, self.entry_id, model.uuid, machine)
            instance_ids[machine.instance_id] = machine_id

        for application in model.applications:
            application_id = await insert_application(self.dbm.db, self.entry_id, model.uuid, application)
            for unit in application.units:
                machine_id = instance_ids.get(unit.machine_instance_id)
                if not machine_id:
                    self.logger.warning(
                        "Missing machine for unit %s in model %s",
                        unit.name,
                        model.uuid,
                    )
                    continue
                await insert_unit(self.dbm.db, self.entry_id, unit, application_id, machine_id)

    async def write_unreachable_model(self, model_id: str):
        await self._ensure_transaction()
        await populate_unreachable_model(self.dbm.db, model_id, self.entry_id)

    async def commit_model(self):
        await self.dbm.commit()

    async def rollback_model(self):
        await self.dbm.rollback()

    async def finalize_controller(self):
        await self._ensure_transaction()
        await insert_juju_data_v1(self.dbm.db, self.dbm.owner_id)
        await self.dbm.commit()

    async def close(self):
        await self.dbm.disconnect()
