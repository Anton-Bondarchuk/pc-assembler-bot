import aiohttp
import logging
import json
from typing import Dict, List, Optional, Any, Type
from urllib.parse import urljoin
import socket

from bot.yandex_market.domain.models.models import (
    PcComponent, Cpu, Gpu, Ram, Storage, Motherboard, PowerSupply, Case, PcBuild
)

logger = logging.getLogger(__name__)

class YandexMarketApiClient:
    """
    Client for interacting with Yandex Market API to fetch PC components.
    """
    
    BASE_URL = "https://api.market.yandex.ru/"
    
    def __init__(self, api_key: str, oauth_token: str, mock_mode: bool = False):
        """
        Initialize the Yandex Market API client.
        
        Args:
            api_key (str): Yandex Market API key
            oauth_token (str): OAuth token for authentication
            mock_mode (bool): If True, use mock data instead of real API calls
        """
        self.api_key = api_key
        self.oauth_token = oauth_token
        self.headers = {
            "Authorization": f"OAuth {oauth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.mock_mode = mock_mode
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Yandex Market API.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            
        Returns:
            Dict: API response data
        """
        if self.mock_mode:
            return self._get_mock_response(endpoint, params)
        
        url = urljoin(self.BASE_URL, endpoint)
        
        if params is None:
            params = {}
        
        # Add API key to params
        params["api_key"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    # Catch DNS and connection errors more gracefully
                    response = await session.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=self.headers,
                        json=data,
                        raise_for_status=True,
                    )
                    return await response.json()
                except aiohttp.ClientConnectorError as e:
                    logger.error(f"Connection error to {url}: {str(e)}")
                    if "Name or service not known" in str(e):
                        raise ConnectionError(f"Cannot connect to host {url.split('//')[1].split('/')[0]} - DNS resolution failed. Check your internet connection or use mock mode for testing.")
                    raise
                    
        except aiohttp.ClientResponseError as e:
            logger.error(f"API error: {e.status}, {e.message}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    def _get_mock_response(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Get mock response data for testing.
        
        Args:
            endpoint (str): API endpoint
            params (Optional[Dict]): Query parameters
            
        Returns:
            Dict: Mock response data
        """
        if 'search' in endpoint:
            query = params.get('text', '') if params else ''
            
            if 'процессор' in query:
                return {
                    "models": [
                        {
                            "id": "cpu1",
                            "name": "Intel Core i7-12700K",
                            "price": {"value": 25000},
                            "link": "https://market.yandex.ru/product/cpu1",
                            "rating": 4.8,
                            "photos": [{"url": "https://example.com/cpu.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Количество ядер", "value": "12 шт"},
                                    {"name": "Частота процессора", "value": "3.6 ГГц"}
                                ]
                            }
                        }
                    ]
                }
            elif 'видеокарта' in query:
                return {
                    "models": [
                        {
                            "id": "gpu1",
                            "name": "NVIDIA GeForce RTX 3080",
                            "price": {"value": 75000},
                            "link": "https://market.yandex.ru/product/gpu1",
                            "rating": 4.9,
                            "photos": [{"url": "https://example.com/gpu.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Объем видеопамяти", "value": "10 ГБ"}
                                ]
                            }
                        }
                    ]
                }
            elif 'память' in query:
                return {
                    "models": [
                        {
                            "id": "ram1",
                            "name": "Kingston HyperX 16GB",
                            "price": {"value": 5000},
                            "link": "https://market.yandex.ru/product/ram1",
                            "rating": 4.7,
                            "photos": [{"url": "https://example.com/ram.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Объем одного модуля", "value": "16 ГБ"},
                                    {"name": "Тип памяти", "value": "DDR4"}
                                ]
                            }
                        }
                    ]
                }
            elif 'накопитель' in query or 'ssd' in query:
                return {
                    "models": [
                        {
                            "id": "storage1",
                            "name": "Samsung 970 EVO 1TB",
                            "price": {"value": 8000},
                            "link": "https://market.yandex.ru/product/storage1",
                            "rating": 4.8,
                            "photos": [{"url": "https://example.com/ssd.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Объем накопителя", "value": "1 ТБ"},
                                    {"name": "Тип накопителя", "value": "SSD"}
                                ]
                            }
                        }
                    ]
                }
            elif 'материнская плата' in query:
                return {
                    "models": [
                        {
                            "id": "mb1",
                            "name": "ASUS ROG STRIX Z590-E",
                            "price": {"value": 20000},
                            "link": "https://market.yandex.ru/product/mb1",
                            "rating": 4.6,
                            "photos": [{"url": "https://example.com/mb.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Сокет", "value": "LGA1200"},
                                    {"name": "Форм-фактор", "value": "ATX"}
                                ]
                            }
                        }
                    ]
                }
            elif 'блок питания' in query:
                return {
                    "models": [
                        {
                            "id": "psu1",
                            "name": "Corsair RM750x",
                            "price": {"value": 10000},
                            "link": "https://market.yandex.ru/product/psu1",
                            "rating": 4.7,
                            "photos": [{"url": "https://example.com/psu.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Мощность", "value": "750 Вт"}
                                ]
                            }
                        }
                    ]
                }
            elif 'корпус' in query:
                return {
                    "models": [
                        {
                            "id": "case1",
                            "name": "NZXT H510",
                            "price": {"value": 7000},
                            "link": "https://market.yandex.ru/product/case1",
                            "rating": 4.5,
                            "photos": [{"url": "https://example.com/case.jpg"}],
                            "specs": {
                                "items": [
                                    {"name": "Форм-фактор", "value": "ATX, microATX, mini-ITX"}
                                ]
                            }
                        }
                    ]
                }
            else:
                return {"models": []}
        elif 'models' in endpoint:
            model_id = endpoint.split('/')[-1]
            return {
                "id": model_id,
                "name": f"Component {model_id}",
                "price": {"value": 10000},
                "link": f"https://market.yandex.ru/product/{model_id}",
                "rating": 4.5,
                "photos": [{"url": f"https://example.com/{model_id}.jpg"}]
            }
        else:
            return {"status": "ok", "data": []}
    
    async def search_components(self, query: str, category_id: Optional[str] = None, price_from: Optional[int] = None, 
                               price_to: Optional[int] = None, limit: int = 10) -> Dict:
        """
        Search for PC components with optional filters.
        
        Args:
            query (str): Search query
            category_id (str, optional): Category ID for filtering
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            limit (int): Maximum number of results
            
        Returns:
            Dict: Search results
        """
        params = {
            "text": query,
            "limit": limit,
        }
        
        if category_id:
            params["categoryId"] = category_id
            
        if price_from is not None:
            params["priceFrom"] = price_from
            
        if price_to is not None:
            params["priceTo"] = price_to
        
        return await self._make_request("GET", "v2/search", params=params)
    
    async def get_component_details(self, model_id: str) -> Dict:
        """
        Get detailed information about a specific component model.
        
        Args:
            model_id (str): Model ID
            
        Returns:
            Dict: Model details
        """
        return await self._make_request("GET", f"v2/models/{model_id}")
    
    def _create_component_from_api_response(self, component_data: Dict, component_class: Type[PcComponent]) -> PcComponent:
        """
        Create a component object from the API response data.
        
        Args:
            component_data (Dict): API response for the component
            component_class (Type[PcComponent]): Component class to instantiate
            
        Returns:
            PcComponent: Component object
        """
        # Extract common fields
        name = component_data.get("name", "")
        price = component_data.get("price", {}).get("value", 0)
        url = component_data.get("link", "")
        rating = component_data.get("rating", 0)
        image_url = ""
        if component_data.get("photos") and len(component_data["photos"]) > 0:
            image_url = component_data["photos"][0].get("url", "")
        
        # Create component instance
        component = component_class(
            name=name,
            price=price,
            url=url,
            rating=rating,
            image_url=image_url
        )
        
        # Extract component-specific details if available
        specs = component_data.get("specs", {})
        if specs and isinstance(component, Gpu):
            for spec in specs.get("items", []):
                if any(keyword in spec.get("name", "").lower() for keyword in ["видеопамяти", "видеопамять", "память", "vram"]):
                    try:
                        vram_str = spec.get("value", "0").split()[0]
                        component.vram = int(float(vram_str))
                    except (ValueError, IndexError):
                        pass
        elif specs and isinstance(component, Cpu):
            for spec in specs.get("items", []):
                if "ядер" in spec.get("name", "").lower():
                    try:
                        component.cores = int(spec.get("value", "0").split()[0])
                    except (ValueError, IndexError):
                        pass
                elif "частот" in spec.get("name", "").lower():
                    try:
                        component.frequency = float(spec.get("value", "0").split()[0])
                    except (ValueError, IndexError):
                        pass
        elif specs and isinstance(component, Ram):
            for spec in specs.get("items", []):
                if "объем" in spec.get("name", "").lower():
                    try:
                        component.capacity = int(spec.get("value", "0").split()[0])
                    except (ValueError, IndexError):
                        pass
                elif "тип" in spec.get("name", "").lower():
                    component.type = spec.get("value", "")
        elif specs and isinstance(component, Storage):
            for spec in specs.get("items", []):
                if "объем" in spec.get("name", "").lower():
                    try:
                        capacity_str = spec.get("value", "0").split()[0]
                        component.capacity = int(float(capacity_str))
                    except (ValueError, IndexError):
                        pass
                elif "тип" in spec.get("name", "").lower():
                    component.type = spec.get("value", "")
        elif specs and isinstance(component, Motherboard):
            for spec in specs.get("items", []):
                if "сокет" in spec.get("name", "").lower():
                    component.socket = spec.get("value", "")
                elif "форм-фактор" in spec.get("name", "").lower():
                    component.form_factor = spec.get("value", "")
        elif specs and isinstance(component, PowerSupply):
            for spec in specs.get("items", []):
                if "мощность" in spec.get("name", "").lower():
                    try:
                        component.wattage = int(spec.get("value", "0").split()[0])
                    except (ValueError, IndexError):
                        pass
        elif specs and isinstance(component, Case):
            for spec in specs.get("items", []):
                if "форм-фактор" in spec.get("name", "").lower():
                    component.form_factor = spec.get("value", "")
                    
        return component
    
    async def get_cpu_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None) -> List[Cpu]:
        """
        Get a list of CPUs within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            
        Returns:
            List[Cpu]: List of CPU objects
        """
        # CPU category ID in Yandex Market
        cpu_category_id = "91013"
        result = await self.search_components("процессор", cpu_category_id, price_from, price_to)
        
        cpus = []
        for model in result.get("models", []):
            cpu = self._create_component_from_api_response(model, Cpu)
            cpus.append(cpu)
        
        return cpus
    
    async def get_gpu_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None) -> List[Gpu]:
        """
        Get a list of GPUs within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            
        Returns:
            List[Gpu]: List of GPU objects
        """
        # GPU category ID in Yandex Market
        gpu_category_id = "91031"
        result = await self.search_components("видеокарта", gpu_category_id, price_from, price_to)
        
        gpus = []
        for model in result.get("models", []):
            gpu = self._create_component_from_api_response(model, Gpu)
            gpus.append(gpu)
        
        return gpus
    
    async def get_ram_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None) -> List[Ram]:
        """
        Get a list of RAM modules within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            
        Returns:
            List[Ram]: List of RAM objects
        """
        # RAM category ID in Yandex Market
        ram_category_id = "91033"
        result = await self.search_components("оперативная память", ram_category_id, price_from, price_to)
        
        rams = []
        for model in result.get("models", []):
            ram = self._create_component_from_api_response(model, Ram)
            rams.append(ram)
        
        return rams
    
    async def get_storage_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None, type_str: Optional[str] = None) -> List[Storage]:
        """
        Get a list of storage devices within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            type_str (str, optional): Type of storage (e.g., "ssd", "hdd")
            
        Returns:
            List[Storage]: List of storage objects
        """
        # Storage category ID in Yandex Market
        storage_category_id = "91033"
        query = type_str if type_str else "накопитель"
        result = await self.search_components(query, storage_category_id, price_from, price_to)
        
        storages = []
        for model in result.get("models", []):
            storage = self._create_component_from_api_response(model, Storage)
            storages.append(storage)
        
        return storages
    
    async def get_motherboard_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None) -> List[Motherboard]:
        """
        Get a list of motherboards within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            
        Returns:
            List[Motherboard]: List of motherboard objects
        """
        # Motherboard category ID in Yandex Market
        mb_category_id = "91020"
        result = await self.search_components("материнская плата", mb_category_id, price_from, price_to)
        
        motherboards = []
        for model in result.get("models", []):
            mb = self._create_component_from_api_response(model, Motherboard)
            motherboards.append(mb)
        
        return motherboards
    
    async def get_power_supply_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None) -> List[PowerSupply]:
        """
        Get a list of power supplies within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            
        Returns:
            List[PowerSupply]: List of power supply objects
        """
        # Power supply category ID in Yandex Market
        psu_category_id = "91028"
        result = await self.search_components("блок питания", psu_category_id, price_from, price_to)
        
        power_supplies = []
        for model in result.get("models", []):
            psu = self._create_component_from_api_response(model, PowerSupply)
            power_supplies.append(psu)
        
        return power_supplies
    
    async def get_case_list(self, price_from: Optional[int] = None, price_to: Optional[int] = None) -> List[Case]:
        """
        Get a list of PC cases within the specified price range.
        
        Args:
            price_from (int, optional): Minimum price
            price_to (int, optional): Maximum price
            
        Returns:
            List[Case]: List of PC case objects
        """
        # Case category ID in Yandex Market
        case_category_id = "91008"
        result = await self.search_components("корпус для компьютера", case_category_id, price_from, price_to)
        
        cases = []
        for model in result.get("models", []):
            pc_case = self._create_component_from_api_response(model, Case)
            cases.append(pc_case)
        
        return cases
    
    async def generate_pc_build(self, budget: int, purpose: str) -> PcBuild:
        """
        Generate a PC build based on budget and intended purpose.
        
        Args:
            budget (int): Total budget for the PC build
            purpose (str): Purpose of the PC (e.g., "gaming", "office", "graphics")
            
        Returns:
            PcBuild: PC build object
        """
        # Map purposes to component allocation percentages
        purpose_allocations = {
            "games": {
                "cpu": 0.20,
                "gpu": 0.35,
                "ram": 0.10,
                "storage": 0.10,
                "motherboard": 0.10,
                "power_supply": 0.08,
                "case": 0.07
            },
            "office": {
                "cpu": 0.25,
                "gpu": 0.10,
                "ram": 0.15,
                "storage": 0.20,
                "motherboard": 0.12,
                "power_supply": 0.08,
                "case": 0.10
            },
            "graphics": {
                "cpu": 0.25,
                "gpu": 0.30,
                "ram": 0.15,
                "storage": 0.12,
                "motherboard": 0.08,
                "power_supply": 0.05,
                "case": 0.05
            },
            "video": {
                "cpu": 0.30,
                "gpu": 0.25,
                "ram": 0.15,
                "storage": 0.15,
                "motherboard": 0.05,
                "power_supply": 0.05,
                "case": 0.05
            },
            "programming": {
                "cpu": 0.30,
                "gpu": 0.10,
                "ram": 0.20,
                "storage": 0.15,
                "motherboard": 0.10,
                "power_supply": 0.08,
                "case": 0.07
            },
            "universal": {
                "cpu": 0.25,
                "gpu": 0.20,
                "ram": 0.15,
                "storage": 0.15,
                "motherboard": 0.10,
                "power_supply": 0.08,
                "case": 0.07
            }
        }
        
        # Map of English purpose keys to Russian terms used in the UI
        purpose_map = {
            "games": "Игры",
            "office": "Офис и учеба",
            "graphics": "Работа с графикой и 3д",
            "video": "Видомонтаж и стримминг",
            "programming": "Программирование",
            "universal": "Универсальный пк"
        }
        
        # Get the English key for the purpose
        purpose_key = next((k for k, v in purpose_map.items() if v == purpose), "universal")
        
        # Get the allocation for the selected purpose, default to universal if not found
        allocation = purpose_allocations.get(purpose_key, purpose_allocations["universal"])
        
        # Create an empty PC build
        pc_build = PcBuild(
            budget_usd=int(budget / 75),
            budget_rub=budget,
            purpose=purpose
        )
        
        # Allocate budget and fetch components
        try:
            cpu_budget = int(budget * allocation["cpu"])
            cpus = await self.get_cpu_list(price_to=cpu_budget)
            if cpus:
                pc_build.cpu = cpus[0]
            
            gpu_budget = int(budget * allocation["gpu"])
            gpus = await self.get_gpu_list(price_to=gpu_budget)
            if gpus:
                pc_build.gpu = gpus[0]
            
            ram_budget = int(budget * allocation["ram"])
            rams = await self.get_ram_list(price_to=ram_budget)
            if rams:
                pc_build.ram = rams[0]
            
            storage_budget = int(budget * allocation["storage"])
            storages = await self.get_storage_list(price_to=storage_budget)
            if storages:
                pc_build.storage = storages[0]
            
            mb_budget = int(budget * allocation["motherboard"])
            motherboards = await self.get_motherboard_list(price_to=mb_budget)
            if motherboards:
                pc_build.motherboard = motherboards[0]
            
            psu_budget = int(budget * allocation["power_supply"])
            power_supplies = await self.get_power_supply_list(price_to=psu_budget)
            if power_supplies:
                pc_build.power_supply = power_supplies[0]
            
            case_budget = int(budget * allocation["case"])
            cases = await self.get_case_list(price_to=case_budget)
            if cases:
                pc_build.case = cases[0]
            
        except Exception as e:
            logger.error(f"Error generating PC build: {str(e)}")
            raise
        
        return pc_build