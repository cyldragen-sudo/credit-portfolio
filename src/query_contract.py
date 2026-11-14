"""Validate demonstration parameter values and render the shipped SQL for verification.

FineReport uses its own parameter widgets; this helper is for repeatable local
verification, not a substitute for runtime parameter validation in FineReport.
"""
import datetime as dt
import re

DEFAULTS = dict(p_as_of='2026-10-31', p_start='2024-11-01', p_end='2026-10-31',
                p_product_id=0, p_channel_id=0, p_region_id=0, p_loan_id=1,
                p_min_dpd=0, p_offset=0, p_risk_id=0)


def render(sql, overrides=None):
    params = dict(DEFAULTS, **(overrides or {}))
    for name, value in params.items():
        if name not in DEFAULTS:
            raise ValueError('Unknown parameter: ' + name)
        if name in ('p_as_of', 'p_start', 'p_end'):
            if dt.date.fromisoformat(str(value)).isoformat() != value:
                raise ValueError('Dates must use YYYY-MM-DD')
        elif type(value) is not int or value < 0:
            raise ValueError('IDs, DPD and offset must be nonnegative integers')
    if not ('2024-11-01' <= params['p_as_of'] <= '2026-10-31'):
        raise ValueError('As-of date is outside the reporting period')
    if params['p_start'] > params['p_end'] or params['p_end'] > params['p_as_of']:
        raise ValueError('Require start <= end <= as-of')
    def substitute(match):
        return str(params[match.group(1)])
    return re.sub(r'\$\{([a-z_]+)\}', substitute, sql)
