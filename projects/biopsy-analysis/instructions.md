# Biopsy Analysis

Use `getIds` to retrieve the patient IDs for this project.
For each ID, use `getEHR` to retrieve the patient's EHR documents.

Goal: identify patients with biopsy-proven malignant disease and summarize
the clinically relevant evidence.

For each patient, report:

- patient ID
- whether a biopsy was performed
- biopsy site and date when available
- pathology result
- malignancy status: malignant, benign, atypical/indeterminate, or unknown
- short evidence summary grounded in the notes

Finish with a compact cohort summary that counts patients by malignancy status.

use the `writeFile` tool to write final report to file. Make sure content is in markdown.
