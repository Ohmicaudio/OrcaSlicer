# Snapmaker Submission Record

## 1. Submission Status

- Innovation Fund form submitted.
- Confirmation text: "You're in. Thanks!"
- Submission contact email: `support@ohmicaudio.com`
- Project name: Adaptive Manufacturing Planner
- Category: Slicer / software
- GitHub/project URL: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>

## 2. Outreach Status

- Email sent to `community@snapmaker.com`.
- Gmail Sent folder confirms message sent.
- Forum post submitted under title: Adaptive Manufacturing Planner for U1: bead widths first, mixed nozzles later
- Forum post approved and public.
- Public forum URL: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359>
- Support ticket submitted through the Snapmaker General Inquiry Form.
- Support ticket subject: U1 engineering guidance request: mixed-nozzle validation constraints for Adaptive Manufacturing Planner
- Support ticket status: awaiting response.
- Reddit `r/snapmaker` Stage 1 benchmark model request posted.
- Reddit URL: <https://www.reddit.com/r/snapmaker/comments/1uiu84u/looking_for_u1_test_models_for_adaptive/>
- Run 001 public update posted to the Snapmaker forum.
- Run 001 forum update URL: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359/11>
- Run 001 public update posted as a comment on the existing Reddit `r/snapmaker` thread.
- Run 001 Reddit update URL: <https://www.reddit.com/r/snapmaker/comments/1uiu84u/comment/ouxk7co/>
- Facebook profile post published and shared to the public Snapmaker U1 Community group.
- Facebook group location: <https://www.facebook.com/groups/2966432890215724/>
- Facebook group share status: visible in group feed; no pending-review or moderation message shown.
- Discord promotion: pending.

## 3. Public Links

- GitHub repo: <https://github.com/Ohmicaudio/OrcaSlicer>
- AMP branch: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>
- Forum URL: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359>
- Reddit URL: <https://www.reddit.com/r/snapmaker/comments/1uiu84u/looking_for_u1_test_models_for_adaptive/>
- Run 001 forum update: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359/11>
- Run 001 Reddit update: <https://www.reddit.com/r/snapmaker/comments/1uiu84u/comment/ouxk7co/>
- Facebook U1 group location: <https://www.facebook.com/groups/2966432890215724/>

## 3a. Run 001 Public Update

- Run 001 used a local CLI-hardened Snapmaker Orca build.
- CLI hardening PR #560: <https://github.com/Snapmaker/OrcaSlicer/pull/560>
- CLI hardening PR #561: <https://github.com/Snapmaker/OrcaSlicer/pull/561>
- CLI hardening PR #562: <https://github.com/Snapmaker/OrcaSlicer/pull/562>
- CLI hardening PRs are separate from AMP planner behavior.
- Benchmark Run 001 remains profile-only.
- Preview and G-code output do not prove print strength.
- Preview and G-code output do not prove surface quality.
- Run 001 does not validate physical mixed-nozzle behavior.

## 4. Current Technical State

- Hidden developer config flag exists.
- No-op AMP planner facade exists.
- Fallback plan value types exist.
- Sidecar cache value types exist.
- Debug artifact value types, serializer, and writer exist.
- Observation summary and observation-to-debug mapper exist.
- Focused AMP tests pass.
- No production slicer path consumes AMP.
- No Snapmaker validation path is bypassed.

## 5. Follow-Up Triggers

- Monitor forum replies and respond with the public GitHub branch, current behavior-neutral status, and Stage 2 hardware-validation request.
- If Snapmaker replies, respond with GitHub branch, roadmap, current test status, and U1 hardware/engineering-feedback request.
- If Snapmaker asks for hardware need, explain Stage 2 requires U1 validation for nozzle-state behavior, toolchange/purge cost, Z-offset/tool calibration, seam behavior, and wall bonding.
