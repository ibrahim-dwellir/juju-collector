from typing import List
import yaml

from domain.models import ControllerConfig

class ConfigReader:
    @staticmethod
    def load_config(path: str) -> List[ControllerConfig]:
        with open(path, 'r') as file:
            data = yaml.safe_load(file) or {}

        return [ControllerConfig(
            controller=item.get('controller', ''),
            username=item.get('username', ''),
            password=item.get('password', ''),
            cacert=item.get('cacert', ''),
            owner_id=item.get('owner_id', 0),
            uuid=item.get('uuid', ''),
            endpoint=item.get('endpoint', ''))  for item in data.get('controllers', [])]
        
