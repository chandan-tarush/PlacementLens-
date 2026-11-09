# Database design

SQLite tables: `workspaces`, `source_files`, `dataset_versions`, `placement_records`, `validation_issues`, `source_claims`, `aggregate_metrics`, `analysis_history`, and `report_history`. Each `placement_records` row stores the canonical record as JSON associated with one immutable `dataset_versions` identifier.
