import logging

from juju.errors import JujuError

from domain.models import Cloud, ControllerInfo
from readers.model_reader import ModelReader
from util.connection_util import connect_to_juju


class CollectorService:
    def __init__(self):
        self.logger = logging.getLogger("CollectorService")

    async def run(self, controller_config, writer):
        controller = None
        try:
            controller = await connect_to_juju(
                controller_config.controller,
                controller_config.username,
                controller_config.password,
                controller_config.cacert,
            )
            self.logger.info(
                "Connected to controller %s", controller_config.controller
            )

            clouds = await self._get_clouds(controller)
            controller_info = ControllerInfo(
                name=controller.controller_name,
                uuid=controller.controller_uuid,
                clouds=clouds,
            )
            await writer.prepare_controller(controller_info)

            models = await controller.model_uuids(all=True)
            for uuid in models.values():
                await self._process_model(writer, controller, uuid)

            try:
                await writer.finalize_controller()
            except Exception:
                self.logger.exception(
                    "Failed to finalize controller %s", controller_config.controller
                )
        finally:
            if writer:
                await writer.close()
            if controller:
                await controller.disconnect()

    async def _process_model(self, writer, controller, uuid):
        try:
            model = await ModelReader(controller, uuid).collect()
        except JujuError:
            self.logger.error("Failed to get model %s", uuid)
            await self._handle_unreachable_model(writer, uuid)
            return
        except ValueError:
            self.logger.info("Skipping model %s", uuid)
            return

        try:
            await writer.write_model(model)
        except Exception:
            self.logger.exception("Failed to write model %s", uuid)
    
    async def _handle_unreachable_model(self, writer, uuid):
        try:
            await writer.write_unreachable_model(uuid)
        except Exception:
            self.logger.exception("Failed to repopulate model %s", uuid)

    async def _get_clouds(self, controller):
        clouds = (await controller.clouds()).clouds.keys()
        return [Cloud(name=cloud[6:]) for cloud in clouds]
