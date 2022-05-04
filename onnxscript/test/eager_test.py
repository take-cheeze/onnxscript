# SPDX-License-Identifier: Apache-2.0

import unittest
import numpy as np
from numpy.testing import assert_almost_equal
from onnxscript.test.models import signal_dft
from onnxscript.test.functions.onnx_script_test_case import (
    OnnxScriptTestCase, FunctionTestParams)


class TestOnnxSignal(OnnxScriptTestCase):

    @staticmethod
    def _fft(x, fft_length, axis=-1):
        ft = np.fft.fft(x, fft_length[0], axis=axis)
        r = np.real(ft)
        i = np.imag(ft)
        merged = np.vstack([r[np.newaxis, ...], i[np.newaxis, ...]])
        perm = np.arange(len(merged.shape))
        perm[:-1] = perm[1:]
        perm[-1] = 0
        tr = np.transpose(merged, list(perm))
        if tr.shape[-1] != 2:
            raise AssertionError(f"Unexpected shape {tr.shape}, x.shape={x.shape} "
                                 f"fft_length={fft_length}.")
        return tr

    @staticmethod
    def _cifft(x, fft_length, axis=-1):
        slices = [slice(0, x) for x in x.shape]
        slices[-1] = slice(0, x.shape[-1], 2)
        real = x[slices]
        slices[-1] = slice(1, x.shape[-1], 2)
        imag = x[slices]
        c = np.squeeze(real + 1j * imag, -1)
        return TestOnnxSignal._ifft(c, fft_length, axis=axis)

    @staticmethod
    def _ifft(x, fft_length, axis=-1):
        ft = np.fft.ifft(x, fft_length[0], axis=axis)
        r = np.real(ft)
        i = np.imag(ft)
        merged = np.vstack([r[np.newaxis, ...], i[np.newaxis, ...]])
        perm = np.arange(len(merged.shape))
        perm[:-1] = perm[1:]
        perm[-1] = 0
        tr = np.transpose(merged, list(perm))
        if tr.shape[-1] != 2:
            raise AssertionError(f"Unexpected shape {tr.shape}, x.shape={x.shape} "
                                 f"fft_length={fft_length}.")
        return tr

    @staticmethod
    def _cfft(x, fft_length, axis=-1):
        slices = [slice(0, x) for x in x.shape]
        slices[-1] = slice(0, x.shape[-1], 2)
        real = x[slices]
        slices[-1] = slice(1, x.shape[-1], 2)
        imag = x[slices]
        c = np.squeeze(real + 1j * imag, -1)
        return TestOnnxSignal._fft(c, fft_length, axis=axis)

    @staticmethod
    def _complex2float(c):
        real = np.real(c)
        imag = np.imag(c)
        x = np.vstack([real[np.newaxis, ...], imag[np.newaxis, ...]])
        perm = list(range(len(x.shape)))
        perm[:-1] = perm[1:]
        perm[-1] = 0
        return np.transpose(x, perm)

    def test_dft_rfft_last_axis(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(5).astype(np.float32).reshape((1, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]

        for onesided in [False, True]:
            for x_ in xs:
                x = x_[..., np.newaxis]
                for s in [4, 5, 6]:
                    le = np.array([s], dtype=np.int64)
                    we = np.array([1] * le[0], dtype=np.float32)
                    expected = self._fft(x_, le)
                    if onesided:
                        slices = [slice(0, a) for a in expected.shape]
                        slices[-2] = slice(0, expected.shape[-2] // 2 + expected.shape[-2] % 2)
                        expected = expected[slices]
                    with self.subTest(x_shape=x.shape, le=list(le),
                                      expected_shape=expected.shape,
                                      onesided=onesided, weights=we):
                        if onesided:
                            case = FunctionTestParams(
                                signal_dft.dft_last_axis, [x, le, we, True], [expected])
                        else:
                            case = FunctionTestParams(
                                signal_dft.dft_last_axis, [x, le, we], [expected])
                        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_dft_cfft_last_axis(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(5).astype(np.float32).reshape((1, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]
        ys = [np.arange(5).astype(np.float32) / 10,
              np.arange(5).astype(np.float32).reshape((1, -1)) / 10,
              np.arange(30).astype(np.float32).reshape((2, 3, -1)) / 10,
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1)) / 10]
        cs = [x + 1j * y for x, y in zip(xs, ys)]

        for c in cs:
            x = self._complex2float(c)
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                we = np.array([1] * le[0], dtype=np.float32)
                expected1 = self._fft(c, le)
                expected2 = self._cfft(x, le)
                assert_almost_equal(expected1, expected2)
                with self.subTest(c_shape=c.shape, le=list(le),
                                  expected_shape=expected1.shape,
                                  weights=we):
                    case = FunctionTestParams(
                        signal_dft.dft_last_axis, [x, le, we, False], [expected1])
                    self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_dft_rfft(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(10).astype(np.float32).reshape((2, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]

        for x_ in xs:
            x = x_[..., np.newaxis]
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                for ax in range(len(x_.shape)):
                    expected = self._fft(x_, le, axis=ax)
                    nax = np.array([ax], dtype=np.int64)
                    with self.subTest(x_shape=x.shape, le=list(le), ax=ax,
                                      expected_shape=expected.shape):
                        case = FunctionTestParams(
                            signal_dft.dft, [x, le, nax], [expected])
                        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_dft_cfft(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(5).astype(np.float32).reshape((1, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]
        ys = [np.arange(5).astype(np.float32) / 10,
              np.arange(5).astype(np.float32).reshape((1, -1)) / 10,
              np.arange(30).astype(np.float32).reshape((2, 3, -1)) / 10,
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1)) / 10]
        cs = [x + 1j * y for x, y in zip(xs, ys)]

        for c in cs:
            x = self._complex2float(c)
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                for ax in range(len(c.shape)):
                    nax = np.array([ax], dtype=np.int64)
                    expected1 = self._fft(c, le, axis=ax)
                    expected2 = self._cfft(x, le, axis=ax)
                    assert_almost_equal(expected1, expected2)
                    with self.subTest(c_shape=c.shape, le=list(le), ax=ax,
                                      expected_shape=expected1.shape):
                        case = FunctionTestParams(
                            signal_dft.dft, [x, le, nax, False], [expected1])
                        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_dft_rifft(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(10).astype(np.float32).reshape((2, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]

        for x_ in xs:
            x = x_[..., np.newaxis]
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                for ax in range(len(x_.shape)):
                    expected = self._ifft(x_, le, axis=ax)
                    nax = np.array([ax], dtype=np.int64)
                    with self.subTest(x_shape=x.shape, le=list(le), ax=ax,
                                      expected_shape=expected.shape):
                        case = FunctionTestParams(
                            signal_dft.idft, [x, le, nax], [expected])
                        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_dft_cifft(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(5).astype(np.float32).reshape((1, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]
        ys = [np.arange(5).astype(np.float32) / 10,
              np.arange(5).astype(np.float32).reshape((1, -1)) / 10,
              np.arange(30).astype(np.float32).reshape((2, 3, -1)) / 10,
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1)) / 10]
        cs = [x + 1j * y for x, y in zip(xs, ys)]

        for c in cs:
            x = self._complex2float(c)
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                for ax in range(len(c.shape)):
                    nax = np.array([ax], dtype=np.int64)
                    expected1 = self._ifft(c, le, axis=ax)
                    expected2 = self._cifft(x, le, axis=ax)
                    assert_almost_equal(expected1, expected2)
                    with self.subTest(c_shape=c.shape, le=list(le), ax=ax,
                                      expected_shape=expected1.shape):
                        case = FunctionTestParams(
                            signal_dft.idft, [x, le, nax, False], [expected1])
                        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_hann_window(self):
        le = np.array([5], dtype=np.int64)
        expected = (np.sin((np.arange(5) * np.pi) / 4) ** 2).astype(np.float32)
        case = FunctionTestParams(signal_dft.hann_window, [le], [expected])
        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_hamming_window(self):
        le = np.array([5], dtype=np.int64)
        alpha = np.array([0.54], dtype=np.float32)
        beta = np.array([0.46], dtype=np.float32)
        expected = alpha - np.cos(np.arange(5) * np.pi * 2 / 4) * beta
        case = FunctionTestParams(signal_dft.hamming_window, [le, alpha, beta], [expected])
        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_blackman_window(self):
        le = np.array([5], dtype=np.int64)
        expected = (
            np.array([0.42]) - np.cos(np.arange(5) * np.pi * 2 / 4) * 0.5 +
            np.cos(np.arange(5) * np.pi * 4 / 4) * 0.08)
        case = FunctionTestParams(signal_dft.blackman_window, [le], [expected])
        self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    @staticmethod
    def _stft(x, fft_length, window, axis=-1, center=False, onesided=False, hop_length=None):
        try:
            import torch
        except ImportError as e:
            raise ImportError("torch is not installed.") from e
        _ = torch.from_numpy
        ft = torch.stft(_(x), n_fft=fft_length, hop_length=hop_length,
                        win_length=fft_length, window=_(window),
                        center=center, onesided=onesided, return_complex=True)
        r = np.real(ft)
        i = np.imag(ft)
        merged = np.vstack([r[np.newaxis, ...], i[np.newaxis, ...]])
        perm = np.arange(len(merged.shape))
        perm[:-1] = perm[1:]
        perm[-1] = 0
        tr = np.transpose(merged, list(perm))
        if tr.shape[-1] != 2:
            raise AssertionError(f"Unexpected shape {tr.shape}, x.shape={x.shape} "
                                 f"fft_length={fft_length}, window={window}.")
        return ft.numpy(), tr.astype(np.float32)

    @staticmethod
    def _istft(y, fft_length, window, axis=-1, center=False, onesided=False, hop_length=None):
        try:
            import torch
        except ImportError as e:
            raise ImportError("torch is not installed.") from e
        _ = torch.from_numpy
        ft = torch.istft(_(y), n_fft=fft_length, hop_length=hop_length,
                        win_length=fft_length, window=_(window),
                        center=center, onesided=onesided, return_complex=True)
        return ft.numpy().astype(np.float32)

    def test_dft_rstft_istft(self):

        xs = [
            ("A0", np.arange(5).astype(np.float32), 5, 1, 1),
            ("A1", np.arange(5).astype(np.float32), 4, 2, 1),
            ("A2", np.arange(5).astype(np.float32), 6, 1, 1),
            ("B0", np.arange(10).astype(np.float32).reshape((2, -1)), 5, 1, 1),
            ("B1", np.arange(10).astype(np.float32).reshape((2, -1)), 4, 2, 1),
            ("B2", np.arange(10).astype(np.float32).reshape((2, -1)), 6, 1, 1),
            ("C0", np.arange(30).astype(np.float32).reshape((6, -1)), 5, 1, 1),
            ("C1", np.arange(30).astype(np.float32).reshape((6, -1)), 4, 2, 1),
            ("C2", np.arange(30).astype(np.float32).reshape((6, -1)), 6, 1, 1),
            ("D0", np.arange(60).astype(np.float32).reshape((6, -1)), 5, 6, 1),
            ("D1", np.arange(60).astype(np.float32).reshape((6, -1)), 4, 7, 1),
            ("D2", np.arange(60).astype(np.float32).reshape((6, -1)), 6, 5, 1),
        ]

        for name, x_, s, fs, hp in xs:
            x = x_[..., np.newaxis]
            le = np.array([s], dtype=np.int64)
            fsv = np.array([fs], dtype=np.int64)
            hpv = np.array([hp], dtype=np.int64)
            window = signal_dft.blackman_window(le)
            window[:] = (np.arange(window.shape[0]) + 1).astype(window.dtype)
            try:
                c_expected, expected = self._stft(x_, le[0], window=window)
            except RuntimeError:
                # unable to validate with torch
                continue
            i_expected = self._istft(c_expected, le[0], window=window)
            info = dict(name=name, x_shape=x.shape, le=list(le), hp=hp, fs=fs,
                        expected_shape=expected.shape, window_shape=window.shape)

            # stft
            with self.subTest(F="STFT", **info):
                # x, fft_length, hop_length, n_frames, window, onesided=False
                case = FunctionTestParams(
                    signal_dft.stft, [x, le, hpv, fsv, window], [expected])
                try:
                    self.run_eager_test(case, rtol=1e-4, atol=1e-4)
                except AssertionError as e:
                    raise AssertionError("Issue with %r." % info) from e

            # istft
            ix = self._complex2float(c_expected)
            if len(x.shape) == 1:
                assert_almost_equal(x[:-1], i_expected)
                expected = x
            elif len(x.shape) == 2:
                if x.shape[1] == 1:
                    assert_almost_equal(x.ravel()[:-1], i_expected.ravel())
                    expected = x.T
                else:
                    assert_almost_equal(x[:, :-1], i_expected)
                    expected = x
            info["expected"] = expected
            info["expected_shape"] = expected.shape
            with self.subTest(F="ISTFT", **info):
                import pprint
                pprint.pprint(info)
                # x, fft_length, hop_length, n_frames, window, onesided=False
                case = FunctionTestParams(
                    signal_dft.istft, [ix, le, hpv, window], expected)
                try:
                    self.run_eager_test(case, rtol=1e-4, atol=1e-4)
                except AssertionError as e:
                    raise AssertionError("Issue with %r." % info) from e

    def test_dft_cstft_istft(self):

        xs = [
            ("A0", np.arange(5).astype(np.float32), 5, 1, 1),
            ("A1", np.arange(5).astype(np.float32), 4, 2, 1),
            ("A2", np.arange(5).astype(np.float32), 6, 1, 1),
            ("B0", np.arange(10).astype(np.float32).reshape((2, -1)), 5, 1, 1),
            ("B1", np.arange(10).astype(np.float32).reshape((2, -1)), 4, 2, 1),
            ("B2", np.arange(10).astype(np.float32).reshape((2, -1)), 6, 1, 1),
            ("C0", np.arange(30).astype(np.float32).reshape((6, -1)), 5, 1, 1),
            ("C1", np.arange(30).astype(np.float32).reshape((6, -1)), 4, 2, 1),
            ("C2", np.arange(30).astype(np.float32).reshape((6, -1)), 6, 1, 1),
            ("D0", np.arange(60).astype(np.float32).reshape((6, -1)), 5, 6, 1),
            ("D1", np.arange(60).astype(np.float32).reshape((6, -1)), 4, 7, 1),
            ("D2", np.arange(60).astype(np.float32).reshape((6, -1)), 6, 5, 1),
        ]

        for name, xy_, s, fs, hp in xs:
            r_ = xy_
            i_ = xy_ / 10
            c_ = r_ + 1j * i_
            x = self._complex2float(c_)
            le = np.array([s], dtype=np.int64)
            fsv = np.array([fs], dtype=np.int64)
            hpv = np.array([hp], dtype=np.int64)
            window = signal_dft.blackman_window(le)
            try:
                c_expected, expected = self._stft(c_, le[0], window=window)
            except RuntimeError:
                # unable to validate with torch
                continue

            i_expected = self._istft(c_expected, le[0], window=window)
            info = dict(name=name, x_shape=x.shape, le=list(le), hp=hp, fs=fs,
                        expected_shape=expected.shape, window_shape=window.shape)

            # stft
            with self.subTest(**info):
                # x, fft_length, hop_length, n_frames, window, onesided=False
                case = FunctionTestParams(
                    signal_dft.stft, [x, le, hpv, fsv, window], [expected])
                try:
                    self.run_eager_test(case, rtol=1e-4, atol=1e-4)
                except AssertionError as e:
                    raise AssertionError("Issue with %r." % info) from e

            # istft
            ix = self._complex2float(c_expected)


if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    TestOnnxSignal().test_dft_rstft_istft()
    unittest.main()
