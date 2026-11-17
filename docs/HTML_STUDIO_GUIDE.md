# HTML Course Studio guide

The current executable workflow is [Studio 2 reproduction](../vlsi-html-course-studio/references/reproduce-v2.md).

- [Course-pack contract](../vlsi-html-course-studio/references/course-pack-contract.md): replace domain, visuals and content without patching the player or production scripts.
- [Migration and versions](../vlsi-html-course-studio/references/migration-v2.md): preserve fidelity, baseline, supported scope and rollback.
- [Current validation](HTML_STUDIO_V2_VALIDATION.md): executed reproduction and its limits.
- [Historical v1 validation](HTML_STUDIO_VALIDATION.md): the original silent starter and portable helper checks.

The old `init_course.py` remains available to reproduce the original 32-second silent prototype. For a complete narrated course, use `studio.py build` with a v2 course pack. The full Placement source snapshot remains an advanced worked example; its historical production scripts are not the new generic CLI.
