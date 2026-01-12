from typing import Iterable

from domain.models import Application, Cloud, ControllerInfo, Machine, Model, Unit


async def setup_juju_temp_tables_v1(db):
    await db.execute("CALL setup_juju_temp_tables_v1()")


async def insert_clouds(db, entry_id: int, clouds: Iterable[Cloud]):
    await db.execute_many(
        "INSERT INTO temp_cloud (row_source, name) VALUES (:entry_id, :name) ON CONFLICT DO NOTHING",
        [{"entry_id": entry_id, "name": cloud.name} for cloud in clouds],
    )


async def insert_controller(db, entry_id: int, controller: ControllerInfo):
    await db.execute(
        "INSERT INTO temp_controller (row_source, name, uuid) VALUES (:entry_id, :name, :uuid)",
        {"entry_id": entry_id, "name": controller.name, "uuid": controller.uuid},
    )


async def insert_model(db, entry_id: int, model: Model):
    await db.execute(
        "INSERT INTO temp_model"
        "   (uuid, name, owner, controller, cloud, row_source)"
        "   VALUES (:uuid, :name, :owner, :controller, :cloud, :entry_id)",
        {
            "uuid": model.uuid,
            "name": model.name,
            "owner": model.owner,
            "controller": model.controller_uuid,
            "cloud": model.cloud,
            "entry_id": entry_id,
        },
    )


async def insert_machine(db, entry_id: int, model_uuid: str, machine: Machine):
    return await db.execute(
        "INSERT INTO temp_machine"
        "    (model, ordinal, ip, instance_id, row_source)"
        "    VALUES (:model, :ordinal, :ip, :instance_id, :entry_id)"
        "    ON CONFLICT (model, ordinal) DO UPDATE SET model = EXCLUDED.model RETURNING id",
        {
            "model": model_uuid,
            "ordinal": machine.ordinal,
            "ip": machine.ip,
            "instance_id": machine.instance_id,
            "entry_id": entry_id,
        },
    )


async def insert_application(db, entry_id: int, model_uuid: str, application: Application):
    return await db.execute(
        "INSERT INTO temp_application"
        "   (model, name, charm, subordinate, row_source)"
        "   VALUES (:model, :name, :charm, :subordinate, :entry_id) RETURNING id",
        {
            "name": application.name,
            "charm": application.charm,
            "subordinate": application.subordinate,
            "model": model_uuid,
            "entry_id": entry_id,
        },
    )


async def insert_unit(db, entry_id: int, unit: Unit, application_id: int, machine_id: int):
    await db.execute(
        "INSERT INTO temp_unit"
        "   (ordinal, name, application, machine, row_source)"
        "   VALUES (:ordinal, :name, :application, :machine, :entry_id)",
        {
            "ordinal": unit.ordinal,
            "name": unit.name,
            "application": application_id,
            "machine": machine_id,
            "entry_id": entry_id,
        },
    )


async def insert_juju_data_v1(db, owner_id: int):
    await db.execute("CALL insert_juju_data_v1(:owner)", {"owner": owner_id})


async def populate_unreachable_model(db, model_id: str, entry_id: int):
    await db.execute(
        f"INSERT INTO temp_model"
        "   (uuid, name, owner, controller, cloud, row_source)"
        "   SELECT uuid, name, owner, controller, cloud, :entry_id FROM model WHERE uuid = :model_id",
        {"entry_id": entry_id, "model_id": model_id},
    )

    await db.execute(
        f"INSERT INTO temp_application"
        "   (id, model, name, charm, subordinate, row_source)"
        "   SELECT id, model, name, charm, subordinate, :entry_id FROM application WHERE model = :model_id",
        {"entry_id": entry_id, "model_id": model_id},
    )

    await db.execute(
        f"INSERT INTO temp_machine"
        "   (id, model, ordinal, ip, instance_id, row_source)"
        "   SELECT id, model, ordinal, ip, instance_id, :entry_id FROM machine WHERE model = :model_id",
        {"entry_id": entry_id, "model_id": model_id},
    )

    await db.execute(
        f"INSERT INTO temp_unit"
        "   (ordinal, name, application, machine, row_source)"
        "   SELECT u.ordinal, u.name, u.application, u.machine, :entry_id FROM unit u JOIN application a ON u.application=a.id WHERE a.model = :model_id",
        {"entry_id": entry_id, "model_id": model_id},
    )
