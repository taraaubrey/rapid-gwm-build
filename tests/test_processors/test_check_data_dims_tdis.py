"""Tests for check_data_dims_tdis processor."""

import numpy as np
import pytest

from rapid_gwm_build.processors.data.checkdims_andor_tdis import (
    check_data_dims_tdis,
)


# Grid dimensions used throughout: nlay=2, nrow=5, ncol=10
NLAY, NROW, NCOL = 2, 5, 10


@pytest.fixture
def idomain():
    return np.ones((NLAY, NROW, NCOL), dtype=int)


# =========================================================================
# A. Scalar expansion
# =========================================================================


class TestScalarExpansion:
    def test_int_to_2d(self, idomain):
        result = check_data_dims_tdis(5, nper=1, idomain=idomain, expected_dims=2)
        assert result.shape == (NROW, NCOL)
        assert result.dtype == int
        assert np.all(result == 5)

    def test_float_to_3d(self, idomain):
        result = check_data_dims_tdis(1e-5, nper=1, idomain=idomain, expected_dims=3)
        assert result.shape == (NLAY, NROW, NCOL)
        assert result.dtype == float
        np.testing.assert_allclose(result, 1e-5)

    def test_float_to_4d(self, idomain):
        result = check_data_dims_tdis(0.001, nper=1, idomain=idomain, expected_dims=4)
        assert result.shape == (1, NLAY, NROW, NCOL)
        assert result.dtype == float
        np.testing.assert_allclose(result, 0.001)

    def test_int_to_4d(self, idomain):
        result = check_data_dims_tdis(1, nper=1, idomain=idomain, expected_dims=4)
        assert result.shape == (1, NLAY, NROW, NCOL)
        assert result.dtype == int
        assert np.all(result == 1)

    def test_scalar_value_preservation(self, idomain):
        """Float scalars preserve exact value (no int truncation)."""
        result = check_data_dims_tdis(3.14, nper=1, idomain=idomain, expected_dims=2)
        np.testing.assert_allclose(result, 3.14)

    def test_scalar_4d_nper_gt1(self, idomain):
        """Scalars can expand to 4D even when nper > 1."""
        result = check_data_dims_tdis(1.0, nper=3, idomain=idomain, expected_dims=4)
        assert result.shape == (3, NLAY, NROW, NCOL)
        np.testing.assert_allclose(result, 1.0)


# =========================================================================
# B. Array identity (ndim == expected_dims)
# =========================================================================


class TestArrayIdentity:
    def test_2d_to_2d(self, idomain):
        data = np.ones((NROW, NCOL))
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=2)
        assert result is data

    def test_3d_to_3d(self, idomain):
        data = np.ones((NLAY, NROW, NCOL))
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)
        assert result is data

    def test_4d_to_4d_nper1(self, idomain):
        data = np.ones((1, NLAY, NROW, NCOL))
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=4)
        assert result is data

    def test_4d_to_4d_nper3(self, idomain):
        data = np.ones((3, NLAY, NROW, NCOL))
        result = check_data_dims_tdis(data, nper=3, idomain=idomain, expected_dims=4)
        assert result is data


# =========================================================================
# C. Array promotion
# =========================================================================


class TestArrayPromotion:
    def test_2d_to_3d_tile_nlay(self, idomain):
        data = np.arange(NROW * NCOL, dtype=float).reshape(NROW, NCOL)
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)
        assert result.shape == (NLAY, NROW, NCOL)
        # Each layer should be identical to input
        np.testing.assert_array_equal(result[0], data)
        np.testing.assert_array_equal(result[1], data)

    def test_2d_to_4d_nper1(self, idomain):
        data = np.ones((NROW, NCOL))
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=4)
        assert result.shape == (1, NLAY, NROW, NCOL)

    def test_3d_to_4d_nper1(self, idomain):
        data = np.ones((NLAY, NROW, NCOL))
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=4)
        assert result.shape == (1, NLAY, NROW, NCOL)
        np.testing.assert_array_equal(result[0], data)

    def test_promotion_preserves_values(self, idomain):
        """Promoted data retains original values."""
        data = np.random.rand(NROW, NCOL)
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=4)
        np.testing.assert_array_equal(result[0, 0], data)
        np.testing.assert_array_equal(result[0, 1], data)


# =========================================================================
# D. Reduction errors
# =========================================================================


class TestReductionErrors:
    def test_3d_to_2d_raises(self, idomain):
        data = np.ones((NLAY, NROW, NCOL))
        with pytest.raises(ValueError, match="Cannot reduce"):
            check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=2)

    def test_4d_to_3d_raises(self, idomain):
        data = np.ones((1, NLAY, NROW, NCOL))
        with pytest.raises(ValueError, match="Cannot reduce"):
            check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)

    def test_4d_to_2d_raises(self, idomain):
        data = np.ones((1, NLAY, NROW, NCOL))
        with pytest.raises(ValueError, match="Cannot reduce"):
            check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=2)


# =========================================================================
# E. nper > 1 promotion errors
# =========================================================================


class TestNperPromotionErrors:
    def test_3d_to_4d_nper_gt1_raises(self, idomain):
        data = np.ones((NLAY, NROW, NCOL))
        with pytest.raises(ValueError, match="nper=3"):
            check_data_dims_tdis(data, nper=3, idomain=idomain, expected_dims=4)

    def test_2d_to_4d_nper_gt1_raises(self, idomain):
        data = np.ones((NROW, NCOL))
        with pytest.raises(ValueError, match="nper=2"):
            check_data_dims_tdis(data, nper=2, idomain=idomain, expected_dims=4)


# =========================================================================
# F. Shape validation errors
# =========================================================================


class TestShapeValidation:
    def test_2d_wrong_shape_raises(self, idomain):
        data = np.ones((NROW + 1, NCOL))
        with pytest.raises(ValueError, match="does not match"):
            check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=2)

    def test_3d_wrong_shape_raises(self, idomain):
        data = np.ones((NLAY + 1, NROW, NCOL))
        with pytest.raises(ValueError, match="does not match"):
            check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)

    def test_4d_wrong_nper_raises(self, idomain):
        data = np.ones((2, NLAY, NROW, NCOL))
        with pytest.raises(ValueError, match="does not match"):
            check_data_dims_tdis(data, nper=3, idomain=idomain, expected_dims=4)


# =========================================================================
# G. Dict input
# =========================================================================


class TestDictInput:
    def test_dict_of_arrays(self, idomain):
        data = {
            "k1": np.ones((NROW, NCOL)),
            "k2": np.ones((NROW, NCOL)) * 2,
        }
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)
        assert isinstance(result, dict)
        assert result["k1"].shape == (NLAY, NROW, NCOL)
        assert result["k2"].shape == (NLAY, NROW, NCOL)
        np.testing.assert_allclose(result["k2"][0], 2.0)

    def test_dict_of_mixed_types(self, idomain):
        data = {
            "scalar": 5.0,
            "array": np.ones((NROW, NCOL)),
        }
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)
        assert result["scalar"].shape == (NLAY, NROW, NCOL)
        assert result["array"].shape == (NLAY, NROW, NCOL)


# =========================================================================
# H. List input
# =========================================================================


class TestListInput:
    def test_list_2d_converts(self, idomain):
        data = [[1.0] * NCOL] * NROW
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=2)
        assert isinstance(result, np.ndarray)
        assert result.shape == (NROW, NCOL)

    def test_list_3d_converts(self, idomain):
        data = [[[1.0] * NCOL] * NROW] * NLAY
        result = check_data_dims_tdis(data, nper=1, idomain=idomain, expected_dims=3)
        assert isinstance(result, np.ndarray)
        assert result.shape == (NLAY, NROW, NCOL)


# =========================================================================
# I. Edge cases
# =========================================================================


class TestEdgeCases:
    def test_invalid_expected_dims_raises(self, idomain):
        with pytest.raises(ValueError, match="expected_dims must be 2, 3, or 4"):
            check_data_dims_tdis(1.0, nper=1, idomain=idomain, expected_dims=5)

    def test_kwargs_passthrough(self, idomain):
        """Extra kwargs don't cause errors."""
        result = check_data_dims_tdis(
            1.0, nper=1, idomain=idomain, expected_dims=2, extra_param="ignored"
        )
        assert result.shape == (NROW, NCOL)
