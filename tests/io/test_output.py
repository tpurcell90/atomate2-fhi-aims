from fhi_aims_workflows.io.outputs import AimsOutput

from .. import TESTDATA_DIR


def test_output():
    filename = TESTDATA_DIR / 'md.out'
    aims_output = AimsOutput(filename)



