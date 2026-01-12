import logging

from domain.models import ControllerInfo, Model


class ConsoleWriter:
    def __init__(self):
        self.logger = logging.getLogger("ConsoleWriter")

    async def prepare_controller(self, controller: ControllerInfo):
        clouds = ", ".join([cloud.name for cloud in controller.clouds]) or "none"
        self.logger.info("Controller: %s (%s)", controller.name, controller.uuid)
        self.logger.info("Clouds: %s", clouds)

    async def write_model(self, model: Model):
        self.logger.info(
            "Model: %s (%s) owner=%s cloud=%s",
            model.name,
            model.uuid,
            model.owner,
            model.cloud,
        )

        if model.machines:
            for machine in sorted(model.machines.values(), key=lambda m: m.ordinal):
                self.logger.info(
                    "  Machine: ordinal=%s instance_id=%s ip=%s",
                    machine.ordinal,
                    machine.instance_id,
                    machine.ip,
                )
        else:
            self.logger.info("  Machines: none")

        if model.applications:
            for application in sorted(model.applications, key=lambda a: a.name):
                self.logger.info(
                    "  Application: %s charm=%s subordinate=%s",
                    application.name,
                    application.charm,
                    application.subordinate,
                )
                if application.units:
                    for unit in sorted(application.units, key=lambda u: u.ordinal):
                        self.logger.info(
                            "    Unit: %s ordinal=%s machine_instance_id=%s",
                            unit.name,
                            unit.ordinal,
                            unit.machine_instance_id,
                        )
                else:
                    self.logger.info("    Units: none")
        else:
            self.logger.info("  Applications: none")

    async def write_unreachable_model(self, model_id: str):
        self.logger.info("Unreachable model: %s (repopulated from DB)", model_id)

    async def commit_model(self):
        return None

    async def rollback_model(self):
        return None

    async def finalize_controller(self):
        return None

    async def close(self):
        return None
