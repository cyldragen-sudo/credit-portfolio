-- Dataset: Filter - Minimum DPD
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct

SELECT * FROM (VALUES (0,'All active'),(1,'1+ DPD'),(31,'31+ DPD'),(91,'91+ DPD')) options(id,label) ORDER BY id
