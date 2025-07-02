"""
Shared test fixtures and configuration.
"""
import pytest
import tempfile
import shutil
import os
from pathlib import Path

@pytest.fixture(scope="session")
def temp_workspace():
    """Create a temporary workspace for tests."""
    temp_dir = tempfile.mkdtemp(prefix="mesh_test_")
    
    # Create test directory structure
    test_dirs = [
        'data',
        'models',
        'scripts'
    ]
    
    for dir_name in test_dirs:
        os.makedirs(os.path.join(temp_dir, dir_name), exist_ok=True)
    
    yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_mesh_files(temp_workspace):
    """Create sample mesh data files."""
    files = {
        'active_domain.shp': 'shapefile content',
        'dem_clipped.tif': 'raster content',
        'basement_z.tif': 'basement raster',
        'simple_top.tif': 'simple top data',
        'simple_bottoms.tif': 'simple bottoms data'
    }
    
    file_paths = {}
    for filename, content in files.items():
        filepath = temp_workspace / 'data' / filename
        with open(filepath, 'w') as f:
            f.write(content)
        file_paths[filename] = str(filepath)
    
    return file_paths