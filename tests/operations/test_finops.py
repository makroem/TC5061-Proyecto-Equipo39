import math
import pytest
from mibici_equipo39.operations.finops import estimate

def test_cost_uses_successful_predictions_and_all_host_cost():
    result=estimate(24, 1000, 60)
    assert result['allocated_test_usd']==pytest.approx(24*60/(730*3600))
    assert result['usd_per_1000_predictions']==pytest.approx(result['allocated_test_usd'])
    assert estimate(24,1000,60,.1)['usd_per_prediction']==pytest.approx(10*result['usd_per_prediction'])

@pytest.mark.parametrize('args',[(24,0,60),(-1,2,60),(24,2,0),(24,2,60,0),(24,2,60,1.1),(24,2,math.nan),(24,True,60)])
def test_undefined_or_invalid_cost_is_rejected(args):
    with pytest.raises(ValueError):
        estimate(*args)
