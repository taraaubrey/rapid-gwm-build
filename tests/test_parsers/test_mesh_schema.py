"""Negative tests for the redesigned mesh schema (dispatcher + structured rules)."""

import pytest

from rapid_gwm_build.nodes.parse.node_schemas import NodeSchemas


def _base_structured():
    """Minimal valid structured mesh config."""
    return {
        'mesh_type': 'structured',
        'nlay': 1,
        'nrow': 10,
        'ncol': 10,
        'resolution': 25,
        'top': 'top.tif',
        'bottoms': 'bottoms.tif',
    }


class TestMeshDispatcher:
    def test_valid_structured_passes(self):
        is_valid, err = NodeSchemas.validate_config('mesh', _base_structured())
        assert is_valid, err

    def test_missing_mesh_type_is_rejected(self):
        cfg = _base_structured()
        del cfg['mesh_type']
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'mesh_type' in err

    def test_unknown_mesh_type_is_rejected(self):
        cfg = _base_structured()
        cfg['mesh_type'] = 'bogus'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'bogus' in err
        assert 'structured' in err  # lists valid values


class TestRenamedFieldErrors:
    def test_active_domain_points_to_domain(self):
        cfg = _base_structured()
        cfg['active_domain'] = 'idomain.arr'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'active_domain' in err and 'domain' in err

    def test_kind_points_to_mesh_type(self):
        cfg = _base_structured()
        cfg['kind'] = 'structured'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'kind' in err and 'mesh_type' in err


class TestEitherOrGroups:
    def test_missing_extent_source_is_rejected(self):
        cfg = _base_structured()
        del cfg['nrow']
        del cfg['ncol']
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'extent_source' in err

    def test_missing_spacing_source_is_rejected(self):
        cfg = _base_structured()
        del cfg['resolution']
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'spacing_source' in err

    def test_extent_source_choices_each_pass(self):
        # Choice 1: extent (file)
        cfg = _base_structured()
        del cfg['nrow']
        del cfg['ncol']
        cfg['extent'] = 'domain.shp'
        assert NodeSchemas.validate_config('mesh', cfg)[0]

        # Choice 3: x_length + y_length
        cfg = _base_structured()
        del cfg['nrow']
        del cfg['ncol']
        cfg['x_length'] = 1000.0
        cfg['y_length'] = 500.0
        assert NodeSchemas.validate_config('mesh', cfg)[0]

    def test_spacing_source_choices_each_pass(self):
        # Choice 2: dx + dy
        cfg = _base_structured()
        del cfg['resolution']
        cfg['dx'] = 10
        cfg['dy'] = 20
        assert NodeSchemas.validate_config('mesh', cfg)[0]

        # Choice 3: delr + delc (requires explicit nrow+ncol which base has)
        cfg = _base_structured()
        del cfg['resolution']
        cfg['delr'] = 'delr.arr'
        cfg['delc'] = 'delc.arr'
        assert NodeSchemas.validate_config('mesh', cfg)[0]

    def test_multiple_spacing_sources_rejected(self):
        cfg = _base_structured()
        cfg['dx'] = 10
        cfg['dy'] = 20
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'spacing_source' in err


class TestMutuallyExclusive:
    def test_extent_plus_nrow_rejected(self):
        cfg = _base_structured()
        cfg['extent'] = 'domain.shp'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'extent' in err and 'nrow' in err

    def test_delr_plus_extent_rejected(self):
        cfg = _base_structured()
        del cfg['nrow']
        del cfg['ncol']
        del cfg['resolution']
        cfg['extent'] = 'domain.shp'
        cfg['delr'] = 'delr.arr'
        cfg['delc'] = 'delc.arr'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid

    def test_delr_plus_x_length_rejected(self):
        cfg = _base_structured()
        del cfg['nrow']
        del cfg['ncol']
        del cfg['resolution']
        cfg['x_length'] = 1000
        cfg['y_length'] = 500
        cfg['delr'] = 'delr.arr'
        cfg['delc'] = 'delc.arr'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid


class TestScalarTypes:
    def test_nlay_must_be_int(self):
        cfg = _base_structured()
        cfg['nlay'] = 'not an int'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'nlay' in err

    def test_angrot_accepts_numeric(self):
        cfg = _base_structured()
        cfg['angrot'] = 45.0
        assert NodeSchemas.validate_config('mesh', cfg)[0]

    def test_xorigin_rejects_string(self):
        cfg = _base_structured()
        cfg['xorigin'] = 'not a number'
        is_valid, err = NodeSchemas.validate_config('mesh', cfg)
        assert not is_valid
        assert 'xorigin' in err
