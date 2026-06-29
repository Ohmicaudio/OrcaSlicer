# Snapmaker Submission Checklist

## A. Project Identity

- Project name: Adaptive Manufacturing Planner
- Tagline: A safety-first path toward geometry-aware manufacturing planning for Snapmaker U1.
- GitHub URL: <https://github.com/Ohmicaudio/OrcaSlicer>
- Project branch URL: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>
- Public community post URL placeholder: `[TBD: Snapmaker community post URL]`
- Contact email: `[confirm public project contact email before submission]`

## B. Current Technical Status

- Hidden developer config flag exists.
- Stock fallback AMP value types exist.
- No-op planner facade exists.
- Sidecar cache value types exist.
- Debug artifact value types exist.
- In-memory JSON serializer exists.
- Standalone debug artifact writer exists.
- Observation summary value types exist.
- Observation-to-debug mapper exists.
- Focused AMP tests currently pass.
- No production slicer path consumes AMP.

## C. What Does Not Exist Yet

- No PrintObject integration.
- No real geometry observation pass.
- No geometry scoring.
- No bead-width influence.
- No Arachne integration.
- No Flow integration.
- No G-code changes.
- No physical mixed-nozzle behavior.

## D. Safety Guardrails

- No Snapmaker validation bypass.
- No `CalibUtils.cpp` bypass.
- No Stage 2 physical mixed-nozzle behavior until U1 hardware access.
- No strength or print-quality claims from preview-only tests.

## E. Submission Sequence

1. Publish repo/fork.
2. Add GitHub URL to final submission docs.
3. Post Snapmaker community thread.
4. Add community post URL to checklist.
5. Submit Snapmaker Innovation Fund form.
6. Send `docs/Snapmaker_Email_Rev2.md` to `community@snapmaker.com` with GitHub link.
7. Keep building benchmark evidence.

## F. Attach/Link These Files

- `README.md`
- `docs/AMP_Branch_Status.md`
- `docs/submission/Snapmaker_Form_Answers_Final.md`
- `docs/submission/Snapmaker_One_Page_Project_Summary_Final.md`
- `docs/submission/Snapmaker_Technical_Appendix_Final.md`
- `docs/benchmarks/AMP_Benchmark_Suite_v0.1.md`
- `docs/risks/AMP_Project_Risk_Register_v0.2.md`
- `docs/U1_Profile_Only_Test_Plan.md`
