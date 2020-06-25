from typing import Dict, Any

from pykitopen.search import SearchResult


class KitOpen:

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def search(self, options: Dict[str, Any]):
        return SearchResult(self.config, options)
