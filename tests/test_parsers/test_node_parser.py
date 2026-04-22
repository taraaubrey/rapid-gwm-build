import pytest

# Import your classes - adjust the import path based on your actual structure
from rapid_gwm_build.nodes.parse.node_parser import NodeParser


class TestMeshParser:
    """Test suite for mesh parsing functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create a NodeParser instance for testing."""
        # Note: Your parser doesn't seem to use node_factory currently
        return NodeParser()
    
    @pytest.fixture
    def valid_mesh_config(self):
        """Valid mesh configuration for testing."""
        return {
            'mesh_type': 'structured',
            'crs': 2193,
            'nlay': 6,
            'nrow': 40,
            'ncol': 20,
            'resolution': 25,
            'domain': {
                'input': 'active_domain.shp',
                'pipeline': [
                    {
                        'processor': 'make_bottom_inactive',
                        'bottoms': '@mesh.bottoms',
                        'inactive_dims': [-2, -1]
                    }
                ]
            },
            'top': 'dem_clipped.tif',
            'bottoms': {
                'input': 'basement_z.tif',
                'pipeline': [
                    {
                        'processor': 'make_layers',
                        'confined_elev': -10,
                        'gravel_elev': -20,
                        'min_thickness': 1,
                        'top': '@mesh.top'
                    }
                ]
            }
        }
    
    # # Test the main _parse_mesh function
    # def test_parse_mesh_creates_correct_structure(self, parser, valid_mesh_config):
    #     """Test that _parse_mesh creates the correct node structure."""
    #     parser._parse_mesh(valid_mesh_config, ['mesh'])

    #     result = parser.node_data[0]
        
    #     # Check main mesh node
    #     assert result['id'] == 'mesh'
    #     assert result['type'] == 'mesh'
    #     assert result['schema_validated'] is True

    
    # def test_is_node_type(self, parser):
        
    #     """Test _is_input_node method."""
    #     assert parser._is_node_type('input', "file.txt") is True
    #     assert parser._is_node_type('input', 123) is True
    #     assert parser._is_node_type('input', {'input': 'file.txt'}) is True
    #     assert parser._is_node_type('input', {'input': {'src': 'file.txt', 'format': 'csv'}}) is True
        
    #     assert parser._is_node_type('input', {'input': {'data': 'file.txt', 'format': 'csv'}}) is False
    #     assert parser._is_node_type('input', {'pipeline': [{'processor': 'test'}]}) is False # this is a failed pipeline
    #     assert parser._is_node_type('input', {'input': 'file.txt', 'builtin': {'top_only': True}}) is False # this is a pipeline
    
        
    #     """Test _is_pipeline_node method."""
    #     assert parser._is_node_type('pipeline', {'pipeline': [{'processor': 'test'}]}) is False
    #     assert parser._is_node_type('pipeline', {'input': 'file.txt'}) is False
    #     assert parser._is_node_type('pipeline', "simple_string") is False
        
    #     assert parser._is_node_type('pipeline', {'input': 'file.txt', 'pipeline': [{'processor': 'test'}]}) is True
    #     assert parser._is_node_type('pipeline', {'input': 'file.txt', 'builtin': {'top_only': True}}) is True
    #     assert parser._is_node_type('pipeline', {'input': {'src': 'file.tif', 'resampling': 'min'}, 'builtin': {'top_only': True}}) is True