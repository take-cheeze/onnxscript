import numpy as np
import unittest
from onnx_script_test_case import FunctionTestParams, OnnxScriptTestCase
from onnxscript.utils import assign_eager_mode_evaluator_to_module
from onnxscript.test.models import if_statement

assign_eager_mode_evaluator_to_module(if_statement, "", 15)


class TestOnnxIf(OnnxScriptTestCase):
    def test_if(self):
        n = 8
        np.random.seed(0)
        a = np.random.rand(n).astype('float32').T
        b = np.random.rand(n).astype('float32').T

        # FIXME(liqunfu): expected are from ort evaluation.
        # needs numpy oxs to provide expected instead.
        expected = np.array([
            0.5488135, 0.71518934, 0.60276335, 0.5448832,
            0.4236548, 0.6458941, 0.4375872, 0.891773], dtype=np.float32)

        cases = [FunctionTestParams(if_statement.maxsum, [a, b], [expected])]
        for case in cases:
            # FAIL : Node () Op (local_function) [TypeInferenceError]
            # GraphProto attribute inferencing is not enabled
            # in this InferenceContextImpl instance.
            # self.run_converter_test(case)
            self.run_eager_test(case)


if __name__ == '__main__':
    unittest.main()