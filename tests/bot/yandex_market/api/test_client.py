import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
from aiohttp import ClientResponseError
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parents[4]  # Go up 4 levels to get to the project root
sys.path.append(str(project_root))

from bot.yandex_market.api.client import YandexMarketApiClient
from bot.yandex_market.domain.models.models import (
    PcComponent, Cpu, Gpu, Ram, Storage, Motherboard, PowerSupply, Case, PcBuild
)
from bot.config_data import config_dict

@pytest.fixture
def api_client():
    """Create a YandexMarketApiClient instance for testing."""
    return YandexMarketApiClient(                     
            api_key=config_dict["yandex_market_api_key"],
            oauth_token=config_dict["yandex_market_oauth_token"]
            )

@pytest.mark.asyncio
async def test_make_request_success(api_client):
    """Test successful API request."""
    mock_response = {"status": "ok", "data": [{"id": 1, "name": "Test"}]}
    
    # Use a simpler mocking approach for the refactored _make_request method
    mock_session = AsyncMock()
    mock_response_obj = AsyncMock()
    mock_response_obj.json = AsyncMock(return_value=mock_response)
    mock_session.request = AsyncMock(return_value=mock_response_obj)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await api_client._make_request("GET", "test_endpoint")
        
    assert result == mock_response
    mock_session.request.assert_called_once()
    # Check that API key is added to params
    assert mock_session.request.call_args[1]["params"]["api_key"] == "test_api_key"


@pytest.mark.asyncio
async def test_make_request_error(api_client):
    """Test handling API request errors."""
    # Simpler mocking approach for the error case
    mock_session = AsyncMock()
    mock_session.request = AsyncMock(side_effect=ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=404,
        message="Not Found"
    ))
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(ClientResponseError):
            await api_client._make_request("GET", "test_endpoint")


@pytest.mark.asyncio
async def test_search_components(api_client):
    """Test searching for components."""
    mock_response = {
        "models": [
            {"id": 1, "name": "Test Component"}
        ]
    }
    
    # Use AsyncMock instead of plain return_value to make the mock callable with assert_called_with
    mock_make_request = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "_make_request", mock_make_request):
        result = await api_client.search_components(
            query="test",
            category_id="123",
            price_from=1000,
            price_to=2000,
            limit=5
        )
    
    # Now this should work
    mock_make_request.assert_called_with(
        "GET", 
        "v2/search", 
        params={
            "text": "test",
            "categoryId": "123",
            "priceFrom": 1000,
            "priceTo": 2000,
            "limit": 5
        }
    )
    assert result == mock_response

@pytest.mark.asyncio
async def test_get_component_details(api_client):
    """Test getting component details."""
    mock_response = {"id": "123", "name": "Test Component"}
    
    # Use AsyncMock
    mock_make_request = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "_make_request", mock_make_request):
        result = await api_client.get_component_details("123")
    
    mock_make_request.assert_called_with("GET", "v2/models/123")
    assert result == mock_response

def test_create_component_from_api_response(api_client):
    """Test creating component objects from API response."""
    # Test with minimal data
    component_data = {
        "name": "Test CPU",
        "price": {"value": 15000}
    }
    
    cpu = api_client._create_component_from_api_response(component_data, Cpu)
    
    assert isinstance(cpu, Cpu)
    assert cpu.name == "Test CPU"
    assert cpu.price == 15000
    
    # Test with complete data
    component_data = {
        "name": "Test GPU",
        "price": {"value": 25000},
        "link": "http://example.com/gpu",
        "rating": 4.5,
        "photos": [{"url": "http://example.com/photo.jpg"}]
    }
    
    gpu = api_client._create_component_from_api_response(component_data, Gpu)
    
    assert isinstance(gpu, Gpu)
    assert gpu.name == "Test GPU"
    assert gpu.price == 25000
    assert gpu.url == "http://example.com/gpu"
    assert gpu.rating == 4.5
    assert gpu.image_url == "http://example.com/photo.jpg"

@pytest.mark.asyncio
async def test_get_cpu_list(api_client):
    """Test getting CPU list."""
    mock_response = {
        "models": [
            {
                "name": "Intel Core i7-11700K",
                "price": {"value": 25000},
                "specs": {
                    "items": [
                        {"name": "Количество ядер", "value": "8 шт"},
                        {"name": "Частота процессора", "value": "3.6 ГГц"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock for search_components
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        cpus = await api_client.get_cpu_list(price_from=20000, price_to=30000)
    
    mock_search_components.assert_called_with("процессор", "91013", 20000, 30000)
    assert len(cpus) == 1
    assert isinstance(cpus[0], Cpu)
    assert cpus[0].name == "Intel Core i7-11700K"
    assert cpus[0].price == 25000
    assert cpus[0].cores == 8
    assert cpus[0].frequency == 3.6

@pytest.mark.asyncio
async def test_get_gpu_list(api_client):
    """Test getting GPU list."""
    mock_response = {
        "models": [
            {
                "name": "NVIDIA GeForce RTX 3080",
                "price": {"value": 75000},
                "specs": {
                    "items": [
                        {"name": "Объем видеопамяти", "value": "10 ГБ"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        gpus = await api_client.get_gpu_list(price_to=80000)
    
    mock_search_components.assert_called_with("видеокарта", "91031", None, 80000)
    assert len(gpus) == 1
    assert isinstance(gpus[0], Gpu)
    assert gpus[0].name == "NVIDIA GeForce RTX 3080"
    assert gpus[0].vram == 10  # This should pass now with our fixed GPU extraction


@pytest.mark.asyncio
async def test_get_ram_list(api_client):
    """Test getting RAM list."""
    mock_response = {
        "models": [
            {
                "name": "Kingston HyperX Fury",
                "price": {"value": 5000},
                "specs": {
                    "items": [
                        {"name": "Объем одного модуля", "value": "16 ГБ"},
                        {"name": "Тип памяти", "value": "DDR4"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        rams = await api_client.get_ram_list()
    
    mock_search_components.assert_called_once()
    assert len(rams) == 1
    assert isinstance(rams[0], Ram)
    assert rams[0].name == "Kingston HyperX Fury"
    assert rams[0].capacity == 16
    assert rams[0].type == "DDR4"

@pytest.mark.asyncio
async def test_get_storage_list(api_client):
    """Test getting storage list."""
    mock_response = {
        "models": [
            {
                "name": "Samsung 970 EVO",
                "price": {"value": 8000},
                "specs": {
                    "items": [
                        {"name": "Объем накопителя", "value": "1 ТБ"},
                        {"name": "Тип накопителя", "value": "SSD"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        storages = await api_client.get_storage_list(type_str="ssd")
    
    mock_search_components.assert_called_with("ssd", "91033", None, None)
    assert len(storages) == 1
    assert isinstance(storages[0], Storage)
    assert storages[0].type == "SSD"

@pytest.mark.asyncio
async def test_get_motherboard_list(api_client):
    """Test getting motherboard list."""
    mock_response = {
        "models": [
            {
                "name": "ASUS ROG STRIX Z590-E GAMING",
                "price": {"value": 20000},
                "specs": {
                    "items": [
                        {"name": "Сокет", "value": "LGA1200"},
                        {"name": "Форм-фактор", "value": "ATX"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        motherboards = await api_client.get_motherboard_list()
    
    mock_search_components.assert_called_once()
    assert len(motherboards) == 1
    assert isinstance(motherboards[0], Motherboard)
    assert motherboards[0].socket == "LGA1200"
    assert motherboards[0].form_factor == "ATX"

@pytest.mark.asyncio
async def test_get_power_supply_list(api_client):
    """Test getting power supply list."""
    mock_response = {
        "models": [
            {
                "name": "Corsair RM750x",
                "price": {"value": 10000},
                "specs": {
                    "items": [
                        {"name": "Мощность", "value": "750 Вт"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        power_supplies = await api_client.get_power_supply_list()
    
    mock_search_components.assert_called_once()
    assert len(power_supplies) == 1
    assert isinstance(power_supplies[0], PowerSupply)
    assert power_supplies[0].wattage == 750

@pytest.mark.asyncio
async def test_get_case_list(api_client):
    """Test getting case list."""
    mock_response = {
        "models": [
            {
                "name": "NZXT H510",
                "price": {"value": 7000},
                "specs": {
                    "items": [
                        {"name": "Форм-фактор", "value": "ATX, microATX, mini-ITX"}
                    ]
                }
            }
        ]
    }
    
    # Use AsyncMock
    mock_search_components = AsyncMock(return_value=mock_response)
    
    with patch.object(api_client, "search_components", mock_search_components):
        cases = await api_client.get_case_list()
    
    mock_search_components.assert_called_once()
    assert len(cases) == 1
    assert isinstance(cases[0], Case)
    assert cases[0].form_factor == "ATX, microATX, mini-ITX"

@pytest.mark.asyncio
async def test_generate_pc_build(api_client):
    """Test generating a complete PC build."""
    # Use AsyncMock for all methods
    mock_get_cpu = AsyncMock(return_value=[Cpu(name="Intel Core i7", price=25000, cores=8, frequency=3.6)])
    mock_get_gpu = AsyncMock(return_value=[Gpu(name="NVIDIA RTX 3080", price=75000, vram=10)])
    mock_get_ram = AsyncMock(return_value=[Ram(name="Kingston 16GB", price=5000, capacity=16, type="DDR4")])
    mock_get_storage = AsyncMock(return_value=[Storage(name="Samsung 1TB SSD", price=8000, capacity=1000, type="SSD")])
    mock_get_mb = AsyncMock(return_value=[Motherboard(name="ASUS ROG", price=20000, socket="LGA1200", form_factor="ATX")])
    mock_get_psu = AsyncMock(return_value=[PowerSupply(name="Corsair 750W", price=10000, wattage=750)])
    mock_get_case = AsyncMock(return_value=[Case(name="NZXT H510", price=7000, form_factor="ATX")])
    
    # Mock all component list methods
    with patch.object(api_client, "get_cpu_list", mock_get_cpu), \
         patch.object(api_client, "get_gpu_list", mock_get_gpu), \
         patch.object(api_client, "get_ram_list", mock_get_ram), \
         patch.object(api_client, "get_storage_list", mock_get_storage), \
         patch.object(api_client, "get_motherboard_list", mock_get_mb), \
         patch.object(api_client, "get_power_supply_list", mock_get_psu), \
         patch.object(api_client, "get_case_list", mock_get_case):
        
        # Call the method to test
        result = await api_client.generate_pc_build(150000, "Игры")
    
    # Verify result
    assert isinstance(result, PcBuild)
    assert result.budget_rub == 150000
    assert result.purpose == "Игры"
    
    # Verify component attributes
    assert result.cpu.name == "Intel Core i7"
    assert result.gpu.name == "NVIDIA RTX 3080"
    assert result.ram.name == "Kingston 16GB"
    assert result.storage.name == "Samsung 1TB SSD"
    assert result.motherboard.name == "ASUS ROG"
    assert result.power_supply.name == "Corsair 750W"
    assert result.case.name == "NZXT H510"
    
    # Verify budget allocation based on purpose
    mock_get_cpu.assert_called_with(price_to=30000)  # 20% of 150000
    mock_get_gpu.assert_called_with(price_to=52500)  # 35% of 150000
    mock_get_ram.assert_called_with(price_to=15000)  # 10% of 150000

@pytest.mark.asyncio
async def test_generate_pc_build_empty_response(api_client):
    """Test handling empty component responses."""
    # Mock all component list methods to return empty lists using AsyncMock
    mock_get_empty = AsyncMock(return_value=[])
    
    # Mock all methods
    with patch.object(api_client, "get_cpu_list", mock_get_empty), \
         patch.object(api_client, "get_gpu_list", mock_get_empty), \
         patch.object(api_client, "get_ram_list", mock_get_empty), \
         patch.object(api_client, "get_storage_list", mock_get_empty), \
         patch.object(api_client, "get_motherboard_list", mock_get_empty), \
         patch.object(api_client, "get_power_supply_list", mock_get_empty), \
         patch.object(api_client, "get_case_list", mock_get_empty):
        
        # Call the method to test
        result = await api_client.generate_pc_build(100000, "Офис и учеба")
    
    # Verify result still has the basic structure but no components
    assert isinstance(result, PcBuild)
    assert result.budget_rub == 100000
    assert result.purpose == "Офис и учеба"
    assert result.cpu is None
    assert result.gpu is None
    assert result.ram is None
    assert result.storage is None
    assert result.motherboard is None
    assert result.power_supply is None
    assert result.case is None

@pytest.mark.asyncio
async def test_generate_pc_build_exception_handling(api_client):
    """Test exception handling in generate_pc_build."""
    # Make get_cpu_list raise an exception
    mock_get_cpu = AsyncMock(side_effect=Exception("API Error"))
    
    with patch.object(api_client, "get_cpu_list", mock_get_cpu):
        with pytest.raises(Exception) as excinfo:
            await api_client.generate_pc_build(100000, "Универсальный пк")
    
    assert "API Error" in str(excinfo.value)