# Course Blueprint

Use this reference for a new course map or a change to its hierarchy. The map is an editable plan, not an instruction to generate every planned artifact.

## Intake for a new map

Get the subject, actual learner level and age range if relevant, learning goal, duration or available hours, any required curriculum or materials, delivery context, and the teacher's chosen story if any. Infer ordinary defaults from the request; ask only for a choice that would materially change the sequence. Do not require a technical track, framework, AI preference, or a fixed number of weeks for unrelated subjects.

## Canonical hierarchy and files

Use `course-plan.json` at the course root as the canonical ordered hierarchy. Keep its `id` fields stable through title and order changes. Store content by ID rather than position so moving a lesson does not change its path:

```text
{course-slug}/
  course-plan.json
  README.md                     # readable, editable table of contents
  style.md                      # shared course visual identity, when media is requested
  marketing/...                 # only when promotional assets are requested
  chapters/{chapter-id}/overview.md
  lessons/{lesson-id}/lesson.md
  lessons/{lesson-id}/notes.md
  lessons/{lesson-id}/notes.pdf
  lessons/{lesson-id}/slides/slides.md
  lessons/{lesson-id}/video/style.md
  lessons/{lesson-id}/video/...
  projects/{project-id}/...
  assets/manifest.json
  assets/...
```

Create only paths needed by the current action. `README.md` lists every section, chapter, lesson, and concept from the map and places chapter and section projects where learners will encounter them. Link to a content file only after it exists; planned items can remain plain text.

## `course-plan.json` contract

The following is the minimum shape. Optional descriptive fields may be added without changing these keys. IDs are globally unique lowercase kebab-case; they do not encode ordering. Artifact names start with a letter and use letters, digits, underscores, or hyphens. `prerequisites` refer to IDs introduced earlier in the ordered map. All `artifacts` values are relative paths inside the course root and name files that exist.

Text, slides, narration, video, and promotional copy can stand alone or work together. Register existing files in `artifacts` on the course, section, chapter, lesson, concept, or project that owns them. When an output uses another output on the same node, record its artifact name in optional `artifactSources`, such as `"narrationAudio": ["narrationText"]`. For another node, use `node-id.artifactName`, such as a course-level `"promo": ["hardware-and-software.lesson"]`. Register supplied files as artifacts too, for example `teacherAudio`. On a source edit, list every affected dependent output in its owner's `staleArtifacts` until it is regenerated and checked, including outputs reached through other dependents. An independent output may have no `artifactSources` entry. Dependency cycles are invalid.

```json
{
  "schemaVersion": 1,
  "id": "computer-foundations",
  "title": "Computer Foundations",
  "subject": "computing",
  "audience": { "level": "absolute beginner" },
  "goal": "Use a computer confidently and begin programming",
  "sections": [
    {
      "id": "computer-essentials",
      "title": "Computer Essentials",
      "outcome": "Use files and common computer tools",
      "chapters": [
        {
          "id": "parts-of-a-computer",
          "title": "Parts of a Computer",
          "outcome": "Identify the main parts and their jobs",
          "prerequisites": [],
          "lessons": [
            {
              "id": "hardware-and-software",
              "title": "Computers, Hardware, and Software",
              "outcome": "Explain what a computer does and distinguish physical parts from programs",
              "prerequisites": [],
              "concepts": [
                { "id": "computer", "title": "Computer", "prerequisites": [] },
                { "id": "hardware", "title": "Hardware", "prerequisites": ["computer"] },
                { "id": "software", "title": "Software", "prerequisites": ["hardware"] }
              ],
              "artifacts": {},
              "artifactSources": {},
              "staleArtifacts": []
            }
          ],
          "project": {
            "id": "label-my-computer",
            "title": "Label My Computer",
            "conceptIds": ["computer", "hardware", "software"],
            "status": "proposed"
          }
        },
        {
          "id": "operating-systems",
          "title": "Operating Systems",
          "outcome": "Use basic system controls",
          "prerequisites": ["hardware-and-software"],
          "lessons": [
            {
              "id": "using-an-os",
              "title": "Using an Operating System",
              "outcome": "Open, switch, and close applications",
              "prerequisites": ["hardware-and-software"],
              "concepts": [
                { "id": "os", "title": "Operating System", "prerequisites": ["software"] }
              ]
            }
          ],
          "project": {
            "id": "explore-my-desktop",
            "title": "Explore My Desktop",
            "conceptIds": ["os"],
            "status": "proposed"
          }
        },
        {
          "id": "files-and-folders",
          "title": "Files and Folders",
          "outcome": "Create and organize files",
          "prerequisites": ["using-an-os"],
          "lessons": [
            {
              "id": "file-types",
              "title": "File Types",
              "outcome": "Recognize files by format and extension",
              "prerequisites": ["using-an-os"],
              "concepts": [
                { "id": "file-format", "title": "File Format", "prerequisites": ["os"] },
                { "id": "file-extension", "title": "File Extension", "prerequisites": ["file-format"] }
              ]
            }
          ],
          "project": {
            "id": "sort-my-files",
            "title": "Sort My Files",
            "conceptIds": ["file-format", "file-extension"],
            "status": "proposed"
          }
        }
      ],
      "project": {
        "id": "organize-my-workspace",
        "title": "Organize My Workspace",
        "conceptIds": ["computer", "hardware", "software", "os", "file-format", "file-extension"],
        "status": "proposed"
      }
    }
  ]
}
```

This minimal example passes the curriculum ordering rules; a real course may contain more sections and lessons. `status` is `proposed`, `selected`, or `developed`; changing status never triggers development on its own.

## Ordering and revision

1. Order sections, chapters, lessons, and concepts by prerequisites. For absolute beginner programming, start with computer hardware and software, operating systems, files and extensions, then tool use and language fundamentals before frameworks.
2. Assign a small tangible project to every chapter. Schedule a larger project at the end of every section. At least three chapter projects precede the first section project. Later section projects increase difficulty and independence.
3. On a reorder request, change array order while preserving IDs; update `README.md`, chapter overviews, navigation, timelines, project prerequisite maps, and affected artifact references. If a move would put a dependency after its use, show the conflict and propose a viable placement rather than silently breaking the sequence. Mark outputs whose content or ordering is now outdated in `staleArtifacts`.
4. After any map edit, run `python <skill-root>/scripts/validate_course.py <course-root>/course-plan.json --sync-toc`. It changes only its marked `README.md` table-of-contents block. Resolve every reported error before finishing. Run validation again after adding artifacts referenced by the map.

The teacher chooses which project to develop next. A proposed title is enough in the map; project details and prompts belong to the separate project action.
