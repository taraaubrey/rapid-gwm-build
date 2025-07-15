import os
import pytest
import yaml
import logging
from unittest.mock import Mock, patch
from copy import deepcopy

# Import your classes - adjust the import path based on your actual structure
from rapid_gwm_build.nodes.parse.node_schemas import NodeSchemas

class TestNodeSchemas:
    """Test suite for NodeSchemas functionality."""

    @pytest.fixture
    def valid_input_config(self):
        """Valid input configuration for testing."""
        return {
            'crs': 2193,
            'nlay': {
                'input': 5
            },
            'resolution': {
                'input': {
                    'src': 25
                }
            },
            'top': {
                'input': {
                    'src': 'test_dem.tif',
                    'resampling': 'min'
                }
            }
        }
    
    @pytest.fixture
    def invalid_input_config(self):
        """Invalid input configuration for testing."""
        return {
            'crs': { # invalid src
                'src': 2193
                },
            'res': {
                'input': {
                    'data': 25,
                    'resampling': 'min'
                },
            },
            'nlay': {
                'input': 5,
                'extra_param': 'unexpected_value',  # invalid extra param
                'pipeline': [
                    {
                        'processor': 'calc_from_res',
                        'resolution': '@resolution.input.src'
                    }
                ],
            },
            'top': {# invalid extra param
                'input': 'test_dem.tif',
                'resampling': 'min' # don't know what to do with this -> raise error
                }
            }

    def test_validate_config_input(self, valid_input_config, invalid_input_config):
        """Test that valid input configuration passes validation."""
        for key, val in valid_input_config.items():
            print(f'Validating key: {key}, value: {val}')
            is_valid, error_msg = NodeSchemas.validate_config('input', val)
            assert is_valid is True

        for key, val in invalid_input_config.items():
            print(f'Validating key: {key}, value: {val}')
            is_valid, error_msg = NodeSchemas.validate_config('input', val)
            assert is_valid is False
    
    def test_validate_config(self):
        data_config = {
            'mesh': 'mesh.tif',
            'cond': 'cond.tif',
            'elev': 'elev.tif',
        }
        
        is_valid, error_msg = NodeSchemas.validate_config('module_data', data_config, all_fields=['mesh', 'cond', 'elev'])
        assert is_valid is True
        
        is_valid, error_msg = NodeSchemas.validate_config('module_data', data_config, all_fields=['mesh', 'flux'])
        assert is_valid is False