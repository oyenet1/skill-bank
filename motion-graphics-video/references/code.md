# Code Quality

Any code a reader or viewer is expected to trust must be **valid, lint-clean, and
actually run**. Snippets written to look plausible are the most common way
teaching material loses credibility — a typo is a dead end for the person
following along.

## Rule

Before shipping any code sample:

1. **Detect the language.**
2. **Run the linter or formatter** for that language.
3. **Fix what it reports** — do not suppress a warning to make it pass.
4. **Typecheck or compile** where the language allows it.
5. **Run it** when it is runnable, and confirm it produces the output the
   material claims.

Report the linter and the result. "Linted clean with `ruff`" is part of the
deliverable; "looks right" is not.

## Tooling per language

| Language | Lint | Format | Verify |
|---|---|---|---|
| JavaScript / TypeScript | `eslint` | `prettier` | `tsc --noEmit` · `node` |
| Python | `ruff check` | `ruff format` / `black` | `python -m py_compile` |
| Go | `go vet` | `gofmt` | `go build` |
| Rust | `cargo clippy` | `rustfmt` | `cargo check` |
| Shell | `shellcheck` | `shfmt` | `bash -n` |
| SQL | `sqlfluff lint` | `sqlfluff fix` | run against a scratch schema |
| CSS | `stylelint` | `prettier` | — |
| HTML | `htmlhint` | `prettier` | — |
| JSON | — | `prettier` | `jq .` |
| YAML | `yamllint` | `prettier` | parse |
| Markdown | `markdownlint` | `prettier` | — |
| Java | `checkstyle` | `google-java-format` | `javac` |
| C / C++ | `clang-tidy` | `clang-format` | compile |
| C# | `dotnet format --verify-no-changes` | `dotnet format` | `dotnet build` |
| PHP | `phpstan` | `php-cs-fixer` | `php -l` |
| Ruby | `rubocop` | `rubocop -a` | `ruby -c` |

Check the toolchain first (the preflight checklist). If a linter is missing,
install it or name the gap — never silently skip the check.

## Writing code for teaching

- **Complete, not truncated.** A snippet that ends in `...` teaches nothing.
  Show the imports, show the closing braces, or say explicitly what is omitted.
- **Minimal.** One concept per snippet. Strip the incidental complexity.
- **Runnable as typed.** The reader should be able to copy it and get the stated
  result. Verify that by running it.
- **Stable output.** If you claim a printed result, run it and paste the real
  output. Never hand-write expected output.
- **No placeholder secrets.** Use obvious fakes like `your-api-key-here`, never
  anything resembling a live credential.
- **Versions named.** State the language and library versions the code targets,
  and check the current API rather than relying on memory.
- **Errors are content.** Show the real error text when teaching debugging; do
  not paraphrase a stack trace.

## In motion graphics and decks

When code appears on screen: use Slidev's Shiki highlighting and step
highlighting — `{1|3|all}` magic-move to show a change, `{monaco}` when the viewer
should be able to edit. Keep lines short enough to read at
delivery size, and never scroll code off the frame in a video.

Lint the code **before** it goes into the deck, not after.
