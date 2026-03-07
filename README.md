# SegLab

SegLab is a desktop application for brain lesion segmentation on T1-weighted MRI with case loading, mask annotation, gold-mask comparison, and attempt-level scoring via Dice and IoU.

## What it does

SegLab provides a single workflow for:

- loading built-in cases or classroom-shared cases
- creating lesion masks
- comparing user masks against gold-standard masks
- scoring segmentation performance
- tracking progress across attempts, cases, and sessions

The current focus is structured lesion-segmentation training in neuroimaging, with a case architecture that also supports later integration of automated segmentation pipelines and human–AI comparison.

## Core functionality

- T1-weighted brain MRI case loading
- built-in and classroom-based case management
- external editor workflow for mask creation
- gold-mask comparison
- Dice and IoU scoring
- per-case history: first, latest, best, delta
- overall progress tracking across cases
- export of attempt-level results
- separate teacher and student workflows

## Use cases

- lesion-segmentation training
- classroom-based annotation exercises
- quantitative skill assessment
- benchmarking of human segmentation performance
- preparation for automated lesion-segmentation evaluation

## Data model

Each case is handled as a structured unit containing:

- source image
- reference mask
- user mask
- case metadata

Each attempt is logged with:

- timestamp
- case ID
- user
- source
- Dice
- IoU
- attempt number

This allows case-level analysis, longitudinal progress tracking, and later extension to model-based inference.

## Repository layout

- `startt_trainer.py` — application entry point
- `ui/` — interface pages and dialogs
- `modules/` — workflow and evaluation logic
- `resources/bundled_cases/` — built-in cases
- `resources/bundled_materials/` — bundled materials
- `build_win.ps1` — Windows build script

## Built-in and classroom cases

SegLab supports two case sources:

**Built-in cases**
- packaged with the application
- intended for fixed offline training sets

**Classroom cases**
- loaded from a shared folder structure
- intended for teacher-controlled distribution of cases

Expected classroom layout:

```text
classrooms/<CLASS_CODE>/cases/<CASE_ID>/
  t1.nii.gz
  gold.nii.gz
  case.json
