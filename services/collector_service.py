import logging

from juju.errors import JujuError

from domain.models import Cloud, ControllerInfo, ControllerConfig
from readers.model_reader import ModelReader
from util.connection_util import connect_to_juju


class CollectorService:
    def __init__(self):
        self.logger = logging.getLogger("CollectorService")

    async def run(self, controller_config: ControllerConfig, writer):
        controller = None
        try:
            controller = await connect_to_juju(
                controller_config.endpoint,
                controller_config.username,
                controller_config.password,
                controller_config.cacert,
            )
            self.logger.info(
                "Connected to controller %s", controller_config.controller
            )

            clouds = await self._get_clouds(controller)
            controller_info = ControllerInfo(
                name=controller_config.controller,
                uuid=controller_config.uuid,
                clouds=clouds,
            )
            await writer.prepare_controller(controller_info)

            models = await controller.model_uuids(all=True)
            for model_uuid in models.values():
                await self._process_model(writer, controller, controller_config.uuid, model_uuid)

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

    async def _process_model(self, writer, controller, controller_uuid, model_uuid):
        try:
            model = await ModelReader(controller, controller_uuid, model_uuid).collect()
        except JujuError:
            self.logger.error("Failed to get model %s", model_uuid)
            await self._handle_unreachable_model(writer, model_uuid)
            return
        except ValueError:
            self.logger.info("Skipping model %s", model_uuid)
            return

        try:
            await writer.write_model(model)
        except Exception:
            self.logger.exception("Failed to write model %s", model_uuid)

    async def _handle_unreachable_model(self, writer, model_uuid):
        try:
            await writer.write_unreachable_model(model_uuid)
        except Exception:
            self.logger.exception("Failed to repopulate model %s", model_uuid)

    async def _get_clouds(self, controller):
        clouds = (await controller.clouds()).clouds.keys()
        return [Cloud(name=cloud[6:]) for cloud in clouds]
