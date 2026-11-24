# Real-question review batch 01

These are **proposals**, not labels. Please edit the JSON block for each row,
confirm every proposed answerability/relevance decision against the pinned
documentation, then tick `Confirmed`. Only tick after you have made the final
decision. Rows left unticked are ignored by the dataset builder.

The Stack Overflow source remains in ignored `data/raw/questions/`; this file
contains only question links and paraphrases, not copied post text.

## Review checklist

- Paraphrase preserves the underlying intent/error while removing identifying
  details; maximum 300 characters.
- For an answerable question, check that the listed pages actually contain the
  relevant answer. Replace paths or mark unanswerable when they do not.
- If the wording is a shortened title rather than a user-authored question,
  change provenance to `synthetic` and explain `derived from <url>` in notes.
- `short_query` is only for 1–3-word wording genuinely present in the source
  title; otherwise use `general`.
- Ensure `mask_pii(query)` would leave the proposed query unchanged.

### Candidate 1 — startup import error

Source: [Stack Overflow question #60819376](https://stackoverflow.com/q/60819376)

Proposed paraphrase: **Why does Uvicorn say it cannot import my FastAPI module when I start the development server?**

Proposed relevant pages: `tutorial/first-steps.md`

Proposed answerable: **Yes** — the first-steps page explains the `module:app` import string and CLI startup.

- [ ] Confirmed

```json
{"source_id":"60819376","source_url":"https://stackoverflow.com/q/60819376","license":"CC BY-SA 4.0","query":"Why does Uvicorn say it cannot import my FastAPI module when I start the development server?","answerable":true,"relevant_source_paths":["tutorial/first-steps.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/60819376"}
```

### Candidate 2 — 422 request validation

Source: [Stack Overflow question #59929028](https://stackoverflow.com/q/59929028)

Proposed paraphrase: **Why does a FastAPI POST request return 422 when I send JSON?**

Proposed relevant pages: `tutorial/body.md`, `tutorial/handling-errors.md`

Proposed answerable: **Yes** — these pages cover request-body declaration, validation, and client-error responses.

- [ ] Confirmed

```json
{"source_id":"59929028","source_url":"https://stackoverflow.com/q/59929028","license":"CC BY-SA 4.0","query":"Why does a FastAPI POST request return 422 when I send JSON?","answerable":true,"relevant_source_paths":["tutorial/body.md","tutorial/handling-errors.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/59929028"}
```

### Candidate 3 — returning an image

Source: [Stack Overflow question #55873174](https://stackoverflow.com/q/55873174)

Proposed paraphrase: **How can a FastAPI endpoint return an image response?**

Proposed relevant pages: `advanced/response-directly.md`, `advanced/custom-response.md`

Proposed answerable: **Yes** — the response documentation describes returning a Starlette response directly and choosing response classes.

- [ ] Confirmed

```json
{"source_id":"55873174","source_url":"https://stackoverflow.com/q/55873174","license":"CC BY-SA 4.0","query":"How can a FastAPI endpoint return an image response?","answerable":true,"relevant_source_paths":["advanced/response-directly.md","advanced/custom-response.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/55873174"}
```

### Candidate 4 — concurrency and request handling

Source: [Stack Overflow question #71516140](https://stackoverflow.com/q/71516140)

Proposed paraphrase: **Why do my FastAPI requests run one after another instead of concurrently?**

Proposed relevant pages: `async.md`, `tutorial/background-tasks.md`

Proposed answerable: **Yes** — the async guide explains concurrency tradeoffs; background tasks cover work that can happen after a response.

- [ ] Confirmed

```json
{"source_id":"71516140","source_url":"https://stackoverflow.com/q/71516140","license":"CC BY-SA 4.0","query":"Why do my FastAPI requests run one after another instead of concurrently?","answerable":true,"relevant_source_paths":["async.md","tutorial/background-tasks.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/71516140"}
```

### Candidate 5 — arbitrary JSON request body

Source: [Stack Overflow question #64379089](https://stackoverflow.com/q/64379089)

Proposed paraphrase: **How can I read and validate any JSON value as a FastAPI request body?**

Proposed relevant pages: `advanced/using-request-directly.md`, `tutorial/body.md`

Proposed answerable: **Yes** — the request reference and body tutorial cover direct body access and typed body models.

- [ ] Confirmed

```json
{"source_id":"64379089","source_url":"https://stackoverflow.com/q/64379089","license":"CC BY-SA 4.0","query":"How can I read and validate any JSON value as a FastAPI request body?","answerable":true,"relevant_source_paths":["advanced/using-request-directly.md","tutorial/body.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/64379089"}
```

### Candidate 6 — running from PyCharm

Source: [Stack Overflow question #62856818](https://stackoverflow.com/q/62856818)

Proposed paraphrase: **How do I configure PyCharm to launch a FastAPI application?**

Proposed relevant pages: none found in the pinned docs.

Proposed answerable: **No** — the pinned docs describe the CLI and editor support but not PyCharm run-configuration setup.

- [ ] Confirmed

```json
{"source_id":"62856818","source_url":"https://stackoverflow.com/q/62856818","license":"CC BY-SA 4.0","query":"How do I configure PyCharm to launch a FastAPI application?","answerable":false,"relevant_source_paths":[],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/62856818"}
```

### Candidate 7 — enum serialization

Source: [Stack Overflow question #65209934](https://stackoverflow.com/q/65209934)

Proposed paraphrase: **Why does converting my Pydantic model to a dictionary keep an enum value instead of a string?**

Proposed relevant pages: `tutorial/extra-data-types.md`

Proposed answerable: **No** — the pinned docs show enum use in FastAPI parameters, but do not explain Pydantic model dump serialization options.

- [ ] Confirmed

```json
{"source_id":"65209934","source_url":"https://stackoverflow.com/q/65209934","license":"CC BY-SA 4.0","query":"Why does converting my Pydantic model to a dictionary keep an enum value instead of a string?","answerable":false,"relevant_source_paths":[],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/65209934"}
```

### Candidate 8 — Uvicorn and Gunicorn workers

Source: [Stack Overflow question #66362199](https://stackoverflow.com/q/66362199)

Proposed paraphrase: **When should I run FastAPI with Uvicorn alone versus Gunicorn with Uvicorn workers?**

Proposed relevant pages: `deployment/server-workers.md`, `deployment/manually.md`

Proposed answerable: **Yes** — the deployment docs describe worker processes and production server choices.

- [ ] Confirmed

```json
{"source_id":"66362199","source_url":"https://stackoverflow.com/q/66362199","license":"CC BY-SA 4.0","query":"When should I run FastAPI with Uvicorn alone versus Gunicorn with Uvicorn workers?","answerable":true,"relevant_source_paths":["deployment/server-workers.md","deployment/manually.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/66362199"}
```

### Candidate 9 — FastAPI and Django integration

Source: [Stack Overflow question #63726203](https://stackoverflow.com/q/63726203)

Proposed paraphrase: **Can a FastAPI application be mounted alongside a Django application?**

Proposed relevant pages: `advanced/wsgi.md`, `advanced/sub-applications.md`

Proposed answerable: **Yes** — the WSGI and sub-application docs explain interoperability and mounting constraints.

- [ ] Confirmed

```json
{"source_id":"63726203","source_url":"https://stackoverflow.com/q/63726203","license":"CC BY-SA 4.0","query":"Can a FastAPI application be mounted alongside a Django application?","answerable":true,"relevant_source_paths":["advanced/wsgi.md","advanced/sub-applications.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63726203"}
```

### Candidate 10 — organizing a larger application

Source: [Stack Overflow question #64943693](https://stackoverflow.com/q/64943693)

Proposed paraphrase: **How should I split a growing FastAPI project into modules and routers?**

Proposed relevant pages: `tutorial/bigger-applications.md`, `reference/apirouter.md`

Proposed answerable: **Yes** — these pages document multi-file applications and APIRouter composition.

- [ ] Confirmed

```json
{"source_id":"64943693","source_url":"https://stackoverflow.com/q/64943693","license":"CC BY-SA 4.0","query":"How should I split a growing FastAPI project into modules and routers?","answerable":true,"relevant_source_paths":["tutorial/bigger-applications.md","reference/apirouter.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/64943693"}
```

### Candidate 11 — default list in a Pydantic model

Source: [Stack Overflow question #63793662](https://stackoverflow.com/q/63793662)

Proposed paraphrase: **How do I give a list field a default value in a FastAPI request model?**

Proposed relevant pages: `tutorial/body.md`, `tutorial/body-fields.md`

Proposed answerable: **Yes** — the request-model docs explain defaults and optional fields.

- [ ] Confirmed

```json
{"source_id":"63793662","source_url":"https://stackoverflow.com/q/63793662","license":"CC BY-SA 4.0","query":"How do I give a list field a default value in a FastAPI request model?","answerable":true,"relevant_source_paths":["tutorial/body.md","tutorial/body-fields.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63793662"}
```

### Candidate 12 — multipart upload with extra data

Source: [Stack Overflow question #65504438](https://stackoverflow.com/q/65504438)

Proposed paraphrase: **How can one FastAPI endpoint accept an uploaded file and accompanying form fields?**

Proposed relevant pages: `tutorial/request-forms-and-files.md`, `tutorial/request-files.md`

Proposed answerable: **Yes** — the combined forms-and-files tutorial addresses multipart request bodies and the JSON limitation.

- [ ] Confirmed

```json
{"source_id":"65504438","source_url":"https://stackoverflow.com/q/65504438","license":"CC BY-SA 4.0","query":"How can one FastAPI endpoint accept an uploaded file and accompanying form fields?","answerable":true,"relevant_source_paths":["tutorial/request-forms-and-files.md","tutorial/request-files.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/65504438"}
```

### Candidate 13 — partial update fields

Source: [Stack Overflow question #67699451](https://stackoverflow.com/q/67699451)

Proposed paraphrase: **How can a PATCH request accept only the fields that should be changed?**

Proposed relevant pages: `tutorial/body-updates.md`

Proposed answerable: **Yes** — the body-update guide covers partial updates and excluding unset fields.

- [ ] Confirmed

```json
{"source_id":"67699451","source_url":"https://stackoverflow.com/q/67699451","license":"CC BY-SA 4.0","query":"How can a PATCH request accept only the fields that should be changed?","answerable":true,"relevant_source_paths":["tutorial/body-updates.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/67699451"}
```

### Candidate 14 — background work and request concurrency

Source: [Stack Overflow question #67599119](https://stackoverflow.com/q/67599119)

Proposed paraphrase: **Can CPU-heavy work in a FastAPI background task delay other requests?**

Proposed relevant pages: `tutorial/background-tasks.md`, `async.md`

Proposed answerable: **Yes** — the background-task caveats distinguish lightweight tasks from heavy work; the async guide covers blocking operations.

- [ ] Confirmed

```json
{"source_id":"67599119","source_url":"https://stackoverflow.com/q/67599119","license":"CC BY-SA 4.0","query":"Can CPU-heavy work in a FastAPI background task delay other requests?","answerable":true,"relevant_source_paths":["tutorial/background-tasks.md","async.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/67599119"}
```

### Candidate 15 — uploading a file

Source: [Stack Overflow question #63048825](https://stackoverflow.com/q/63048825)

Proposed paraphrase: **What is the documented way to receive an uploaded file in FastAPI?**

Proposed relevant pages: `tutorial/request-files.md`, `reference/uploadfile.md`

Proposed answerable: **Yes** — these pages explain `File`, `UploadFile`, and file request handling.

- [ ] Confirmed

```json
{"source_id":"63048825","source_url":"https://stackoverflow.com/q/63048825","license":"CC BY-SA 4.0","query":"What is the documented way to receive an uploaded file in FastAPI?","answerable":true,"relevant_source_paths":["tutorial/request-files.md","reference/uploadfile.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63048825"}
```

### Candidate 16 — custom decorators on routes

Source: [Stack Overflow question #64497615](https://stackoverflow.com/q/64497615)

Proposed paraphrase: **How can I add a custom decorator around a FastAPI path operation without breaking routing?**

Proposed relevant pages: `how-to/custom-request-and-route.md`, `tutorial/dependencies/index.md`

Proposed answerable: **No** — the docs cover custom APIRoute classes and dependencies, not arbitrary Python decorator wrapping patterns.

- [ ] Confirmed

```json
{"source_id":"64497615","source_url":"https://stackoverflow.com/q/64497615","license":"CC BY-SA 4.0","query":"How can I add a custom decorator around a FastAPI path operation without breaking routing?","answerable":false,"relevant_source_paths":[],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/64497615"}
```

### Candidate 17 — slash redirect status

Source: [Stack Overflow question #70351360](https://stackoverflow.com/q/70351360)

Proposed paraphrase: **Why does requesting a FastAPI route with a trailing slash produce a 307 redirect?**

Proposed relevant pages: none found in the pinned docs.

Proposed answerable: **No** — the pinned docs do not explain Starlette's slash-normalization redirect behavior.

- [ ] Confirmed

```json
{"source_id":"70351360","source_url":"https://stackoverflow.com/q/70351360","license":"CC BY-SA 4.0","query":"Why does requesting a FastAPI route with a trailing slash produce a 307 redirect?","answerable":false,"relevant_source_paths":[],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/70351360"}
```

### Candidate 18 — outbound HTTP calls

Source: [Stack Overflow question #63872924](https://stackoverflow.com/q/63872924)

Proposed paraphrase: **How should a FastAPI endpoint call an external HTTP API asynchronously?**

Proposed relevant pages: `async.md`

Proposed answerable: **No** — the corpus explains async scheduling but does not document an outbound HTTP client or its API.

- [ ] Confirmed

```json
{"source_id":"63872924","source_url":"https://stackoverflow.com/q/63872924","license":"CC BY-SA 4.0","query":"How should a FastAPI endpoint call an external HTTP API asynchronously?","answerable":false,"relevant_source_paths":[],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63872924"}
```

### Candidate 19 — client IP behind a proxy

Source: [Stack Overflow question #60098005](https://stackoverflow.com/q/60098005)

Proposed paraphrase: **How can FastAPI determine a client's original IP address behind a reverse proxy?**

Proposed relevant pages: `advanced/behind-a-proxy.md`

Proposed answerable: **Yes** — the proxy guide describes forwarded headers and trusted proxy configuration.

- [ ] Confirmed

```json
{"source_id":"60098005","source_url":"https://stackoverflow.com/q/60098005","license":"CC BY-SA 4.0","query":"How can FastAPI determine a client's original IP address behind a reverse proxy?","answerable":true,"relevant_source_paths":["advanced/behind-a-proxy.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/60098005"}
```

### Candidate 20 — HTTPS-aware redirects

Source: [Stack Overflow question #63511413](https://stackoverflow.com/q/63511413)

Proposed paraphrase: **Why does a FastAPI trailing-slash redirect use HTTP instead of HTTPS behind a proxy?**

Proposed relevant pages: `advanced/behind-a-proxy.md`, `deployment/https.md`

Proposed answerable: **Yes** — the proxy and HTTPS docs describe forwarded scheme headers and proxy trust settings.

- [ ] Confirmed

```json
{"source_id":"63511413","source_url":"https://stackoverflow.com/q/63511413","license":"CC BY-SA 4.0","query":"Why does a FastAPI trailing-slash redirect use HTTP instead of HTTPS behind a proxy?","answerable":true,"relevant_source_paths":["advanced/behind-a-proxy.md","deployment/https.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63511413"}
```

### Candidate 21 — `None` as a default

Source: [Stack Overflow question #63616798](https://stackoverflow.com/q/63616798)

Proposed paraphrase: **How does FastAPI treat a model field whose default value is `None`?**

Proposed relevant pages: `tutorial/body.md`, `tutorial/query-params.md`

Proposed answerable: **Yes** — these pages explain defaults, required parameters, and optional values.

- [ ] Confirmed

```json
{"source_id":"63616798","source_url":"https://stackoverflow.com/q/63616798","license":"CC BY-SA 4.0","query":"How does FastAPI treat a model field whose default value is `None`?","answerable":true,"relevant_source_paths":["tutorial/body.md","tutorial/query-params.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63616798"}
```

### Candidate 22 — dependency injection versus direct calls

Source: [Stack Overflow question #61871147](https://stackoverflow.com/q/61871147)

Proposed paraphrase: **What does FastAPI's `Depends` mechanism add compared with calling the same helper directly?**

Proposed relevant pages: `tutorial/dependencies/index.md`, `tutorial/dependencies/sub-dependencies.md`

Proposed answerable: **Yes** — the dependency guide explains resolution, reuse, and nested dependencies.

- [ ] Confirmed

```json
{"source_id":"61871147","source_url":"https://stackoverflow.com/q/61871147","license":"CC BY-SA 4.0","query":"What does FastAPI's `Depends` mechanism add compared with calling the same helper directly?","answerable":true,"relevant_source_paths":["tutorial/dependencies/index.md","tutorial/dependencies/sub-dependencies.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/61871147"}
```

### Candidate 23 — catch-all path parameter

Source: [Stack Overflow question #63069190](https://stackoverflow.com/q/63069190)

Proposed paraphrase: **How can one FastAPI route capture the remaining path segments after a prefix?**

Proposed relevant pages: `tutorial/path-params.md`, `reference/parameters.md`

Proposed answerable: **Yes** — the path-parameter docs describe the path converter for capturing slash-containing values.

- [ ] Confirmed

```json
{"source_id":"63069190","source_url":"https://stackoverflow.com/q/63069190","license":"CC BY-SA 4.0","query":"How can one FastAPI route capture the remaining path segments after a prefix?","answerable":true,"relevant_source_paths":["tutorial/path-params.md","reference/parameters.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63069190"}
```

### Candidate 24 — multiprocessing for CPU-bound work

Source: [Stack Overflow question #63169865](https://stackoverflow.com/q/63169865)

Proposed paraphrase: **How can a FastAPI request use multiple CPU cores for a CPU-bound task?**

Proposed relevant pages: `async.md`, `deployment/server-workers.md`

Proposed answerable: **No** — the docs cover async and server workers, but not per-request multiprocessing design.

- [ ] Confirmed

```json
{"source_id":"63169865","source_url":"https://stackoverflow.com/q/63169865","license":"CC BY-SA 4.0","query":"How can a FastAPI request use multiple CPU cores for a CPU-bound task?","answerable":false,"relevant_source_paths":[],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/63169865"}
```

### Candidate 25 — global exception handling

Source: [Stack Overflow question #61596911](https://stackoverflow.com/q/61596911)

Proposed paraphrase: **How can I register a global handler for unexpected exceptions in FastAPI?**

Proposed relevant pages: `tutorial/handling-errors.md`

Proposed answerable: **Yes** — the error-handling guide documents application-level exception handlers.

- [ ] Confirmed

```json
{"source_id":"61596911","source_url":"https://stackoverflow.com/q/61596911","license":"CC BY-SA 4.0","query":"How can I register a global handler for unexpected exceptions in FastAPI?","answerable":true,"relevant_source_paths":["tutorial/handling-errors.md"],"slice":"general","provenance":"real","notes":"paraphrased; attribution: https://stackoverflow.com/q/61596911"}
```
