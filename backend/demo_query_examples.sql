-- 1) Active factories in pincode 560058 with no inspection in last 18 months
SELECT u.ubid, u.business_name, u.pincode, s.status, MAX(e.event_ts) AS last_inspection_ts
FROM ubid_registry u
JOIN ubid_activity_status s ON s.ubid = u.ubid
LEFT JOIN business_events e
  ON e.ubid = u.ubid
 AND e.event_type = 'inspection'
WHERE u.department_category = 'factory'
  AND u.pincode = '560058'
  AND s.status = 'Active'
GROUP BY u.ubid, u.business_name, u.pincode, s.status
HAVING MAX(e.event_ts) IS NULL
   OR MAX(e.event_ts) < (CURRENT_DATE - INTERVAL '18 months');

-- 2) UBIDs with conflicting PAN values among linked records
SELECT m.ubid, COUNT(DISTINCT r.pan) AS distinct_pan_count
FROM ubid_record_map m
JOIN source_records r ON r.source_record_id = m.source_record_id
WHERE r.pan IS NOT NULL AND r.pan <> ''
GROUP BY m.ubid
HAVING COUNT(DISTINCT r.pan) > 1;

-- 3) Dormant businesses with high recent utility usage (possible anomaly)
SELECT s.ubid, s.status, f.utility_kwh_90d, f.last_filing_days_ago
FROM ubid_activity_status s
JOIN ubid_activity_features f ON f.ubid = s.ubid
WHERE s.status = 'Dormant'
  AND f.utility_kwh_90d > 1000
ORDER BY f.utility_kwh_90d DESC;
