from os import environ
from logging import getLogger
from typing import Dict
from juju.controller import Controller
from juju.application import Application
from juju.errors import JujuError

from domain.models import Application as AppModel
from domain.models import Machine, Model, Unit

logger = getLogger(__name__)

class ModelReader:
    def __init__(self, controller: Controller, uuid):
        self.controller = controller
        self.uuid = uuid
        self.name = ""
        self.owner = ""
        self.cloud = ""
        self.controller_uuid = ""
        self.applications = []
        self.machines: Dict[str, Machine] = {}

    def add_application(self, application: Application):
        units = [
            Unit(
                ordinal=int(unit.name.split("/")[1]),
                name=unit.name,
                machine_instance_id=self.add_machine(unit.machine, unit.public_address),
            )
            for unit in application.units
        ]
        self.applications.append(
            AppModel(
                name=application.name,
                charm=application.charm_name,
                subordinate=application.subordinate,
                units=units,
            )
        )

    def add_machine(self, machine, public_address):
        """
        A side-effectful method that adds a machine if not already recorded in the machines dictionary.
        Returns the machine id.
        """
        if machine.instance_id not in self.machines:
            self.machines[machine.instance_id] = Machine(
                ordinal=int(machine.id),
                ip=self.machine_ip(machine, public_address),
                instance_id=machine.instance_id,
            )

        return machine.instance_id

    def machine_ip(self, machine, public_address):
        """
        Empirically speaking juju can report a lot of faulty IP addresses. This logic attempts to pick the right one based on a number of criteria.

        * Juju has access to a basket of IP addresses for any one machine. These are classified by scope and type.
        * Some of these are ipv6 addresses, som ipv4. Some are local to the cloud, some are public, and some are locla to the machine.
        * The logic here works as follows:
            1. If an IP address belongs to a "preferred prefix" (default: 192.168), it is preferred and "wins".
            2. If no IP address belongs to a preferred prefix, the first IP address that is not in a banned prefix (default: 172.17) is chosen.
            3. If no IP address is found in the above steps, the public address is chosen (necessary for some manually providioned machines).
            4. If no public address is found, None is returned.
        """
        try:
            permitted_scopes = environ.get("PERMITTED_IP_SCOPES") or ["local-cloud"]
            permitted_types = environ.get("PERMITTED_IP_TYPES") or ["ipv4"]
            addresses = [address["value"] for address in machine.addresses if address["scope"] in permitted_scopes and address["type"] in permitted_types]
            preferred = [address for address in addresses if address.startswith(environ.get("PREFERRED_IP_PREFIX") or "192.168")]
            permissible = [address for address in addresses if not address.startswith(environ.get("BANNED_IP_PREFIX") or "172.17")]
            return preferred[0] if preferred else permissible[0] if permissible else public_address
        except (IndexError, AttributeError):
            logger.warning(
                "Failed to get IP address for machine %s:%s",
                self.uuid,
                machine.instance_id,
            )
            return None

    async def collect(self):
        try:
            model = await self.controller.get_model(self.uuid)
        except JujuError:
            logger.error(f"Failed to do get_model on {self.uuid}")
            raise

        if model.info.provider_type not in ["lxd", "manual"]:
            logger.info(f"Skipping model {self.uuid} ({model.info.name}) because it is not an lxd or manual model.")
            raise ValueError(f"Model {self.uuid} is not an lxd or manual model.")
        
        self.name = model.info.name
        self.owner = model.info.owner_tag[5:]
        self.cloud = model.info.cloud_tag[6:]
        self.controller_uuid = self.controller.controller_uuid
        logger.info(f"Collecting data for model {self.uuid} ({self.name})")
        for application in model.applications.values():
            self.add_application(application)
            logger.info(f"Collected data for application {self.uuid}:{application.name}")
        return Model(
            uuid=self.uuid,
            name=self.name,
            owner=self.owner,
            controller_uuid=self.controller_uuid,
            cloud=self.cloud,
            applications=self.applications,
            machines=self.machines,
        )
