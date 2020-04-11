WITH sq_count as (
    select count(*) as count, half_hour(time) as hh, pluscode from update_log group by hh, pluscode
)
INSERT INTO grid(time, pluscode, attributes) 
    SELECT sq_count.hh, sq_count.pluscode, 
           hstore('count', sq_count.count::text)
FROM sq_count;

UPDATE grid SET
    attributes = attributes || hstore('sick', (count > 0)::text)
FROM (
    select count(*) as count, half_hour(time) as hh, pluscode from update_log 
    where attributes->'feels_sick' = 'True'
    group by hh, pluscode
) sq_sick
WHERE grid.time = sq_sick.hh AND grid.pluscode = sq_sick.pluscode;

UPDATE grid SET
    attributes = attributes || hstore('sick', (count = 0)::text)
FROM (
    select count(*) as count, half_hour(time) as hh, pluscode from update_log 
    where attributes->'feels_sick' = 'False'
    group by hh, pluscode
) sq_sick
WHERE grid.time = sq_sick.hh AND grid.pluscode = sq_sick.pluscode;
