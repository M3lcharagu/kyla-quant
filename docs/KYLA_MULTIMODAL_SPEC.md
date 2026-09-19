# KYLA Multimodal Interface Specification

**Status:** implementation specification / New KYLA spec track  
**Target stack:** Mel's iPhone 11, 2012 MacBook, and WhatsApp as the primary transport  
**Assumptions:** a small home Mac service can be kept running, the phone can upload attachments or record voice notes, and provider credentials may be added later. Exact 2012 Mac model, RAM, storage type, network quality, and available adapters are not assumed.

## 1. Scope and explicit constraints

KYLA's multimodal interface is an attachment-first system with optional low-frequency desktop capture and voice interaction. It is intended to see and understand:

- Images, screenshots, camera photos, chart/error-message/design captures, and TradingView setups.
- PDFs and DOC/DOCX files, including extracted text, OCR, page images, diagrams, and tables.
- Video, including YouTube/TikTok links when the content can be accessed, downloaded, or sampled legally and technically.
- macOS screen captures taken by an explicit local capture process.
- Audio voice notes and, separately, microphone input when the user deliberately enables it.

**WhatsApp is the primary transport.** A WhatsApp adapter must receive an attachment or message, download it into a short-lived work area, classify and process it, return a text/voice response or a dashboard link, and delete it according to retention policy. WhatsApp does not by itself give an LLM continuous access to a phone display.

### Three different visual capabilities

| Capability | Meaning | Build status on this stack | Default policy |
|---|---|---|---|
| Attachment processing | User sends a photo, screenshot, PDF, DOC, video, or audio file. KYLA processes that finite artifact. | Buildable now; best first milestone | Explicit user action; retain temporarily only |
| Continuous vision | A repeated stream of stills or sensor frames is analyzed over time. | Buildable on the Mac with throttling; not a phone default | Opt-in, low frequency, visible indicator, automatic stop |
| Live screen share | A live display stream is delivered from a device to a model/service. | Not available from an iPhone 11 to an LLM without an app/integration. A Mac capture agent can approximate it. | Never imply that a WhatsApp attachment is live access |

The iPhone 11 can take or send camera photos, screenshots, recordings, and voice notes. It cannot silently expose its system-level live screen to KYLA through WhatsApp. A dedicated iOS app, an approved screen-capture integration, or user-driven screenshots would be required for a true phone screen stream.

### Privacy, consent, and trading-risk boundaries

- Every capture mode has a visible state: **off**, **one-shot**, **scheduled**, or **live/continuous**. Microphone and screen capture require an explicit enable action and can be stopped immediately.
- Do not upload unrelated people, private conversations, credentials, API keys, seed phrases, account numbers, or unredacted secrets. Apply local redaction where feasible and reject or warn on likely secrets.
- Treat media and links as untrusted input. Do not execute files, follow instructions embedded in an image/PDF, or let a transcript override system policy.
- Visual/audio/video interpretation is probabilistic. Preserve provenance (source, timestamp, transformations, model, and confidence) and expose uncertainty.
- KYLA must not place or modify a trade based solely on an image, audio, or video interpretation. A separate data adapter, rule engine, and explicit confirmation gate are required. A chart screenshot can produce an analysis, never an autonomous order.

## 2. Visual input

### 2.1 Buildable inputs and processing

#### (a) Screenshots: charts, errors, designs, and TradingView

A screenshot is the highest-value first feature. The pipeline should normalize orientation and size, compute a hash, run local OCR for text and numeric labels, then send the image plus extracted text to a vision-capable model when enabled. The semantic step can identify chart regions, indicator names, visible levels, error messages, layout relationships, and design affordances; it must not claim values that are cropped or unreadable.

For TradingView, KYLA can describe visible structure (for example, trend, support/resistance candidates, apparent indicator state, and whether a screenshot appears to satisfy SSS/BBB rules) and report which rule inputs are missing. It cannot safely infer exact live prices, position state, or news from pixels. Those require a timestamped market/position/news adapter.

Recommended response fields: `observed`, `inferred`, `not_visible`, `rule_checks`, `confidence`, `timestamp`, and `action: no_trade` unless an independent confirmed workflow says otherwise.

#### (b) PDFs and DOC/DOCX

Use a two-track extractor:

1. Extract text, metadata, headings, tables, and page numbers with a sandboxed parser. Run OCR on image-only pages.
2. Render each relevant page to a bounded-resolution image so diagrams, screenshots, forms, and layout relationships are available to a vision step.

Text extraction/OCR is not semantic vision: OCR says which characters are likely present; a vision model reasons over the rendered page and its visual relationships. Keep page references and quote small source spans so answers are auditable. Reject macros, active content, and external references rather than executing them.

#### (c) YouTube/TikTok links

When the platform and user authorization permit access, fetch a transcript/captions track and sample frames at a bounded rate (for example, scene changes plus one frame every 5–15 seconds). Combine transcript chunks with frame timestamps. If the video is private, login-gated, deleted, rate-limited, blocked by anti-bot controls, or not legally retrievable, return a partial result or ask the user to upload an authorized copy.

A transcript is not visual understanding. KYLA must compare spoken claims to sampled frames and label claims that have no visual evidence. Copyright, platform terms, creator rights, and local law govern downloading, storage, and re-use. Do not promise that every link can be fetched.

#### (d) macOS screen capture

A local Mac agent can invoke the native `screencapture` command for a one-shot or low-frequency still capture, then pass the still through the same OCR and vision pipeline. A practical initial loop is:

```text
user enables Desktop Watch
  -> launch agent records state + visible indicator
  -> screencapture captures one selected display/window every 10–30 seconds
  -> resize/compress and redact configured regions locally
  -> OCR locally; optionally call vision API
  -> compare with prior hash; skip unchanged frames
  -> retain only the latest N frames and derived result
  -> stop on timeout, user command, sleep, logout, or error
```

Start at 30 seconds, capture only a chosen window if possible, and use event-triggered one-shots for alerts. This is not a live video stream. macOS privacy controls may require Screen Recording permission for the terminal, launch agent, or packaged app that performs the capture; permissions are per app/process and can fail after a binary or path changes. The setup must detect a permission failure and explain it instead of retrying indefinitely. Captures can include passwords and other people, so use an allowlist of windows and redaction.

#### (e) iPhone camera and photo attachments

WhatsApp photo/document attachments are the default iPhone path. The adapter should preserve the original MIME type where safe, normalize EXIF orientation, strip unnecessary EXIF/GPS metadata before external upload, generate a thumbnail, and cap pixel dimensions for processing. Camera photos are suitable for whiteboards, physical documents, product/design references, and screenshots photographed from another screen; glare, blur, perspective, and low light must lower confidence.

### 2.2 Effort/value ranking

| Rank | Input | Value for Mel's stack | Effort | Why |
|---:|---|---|---|---|
| 1 | WhatsApp screenshots/photos | High | Low | Uses the existing phone and transport; no continuous permissions |
| 2 | PDF/DOC text + OCR + page rendering | High | Low–medium | Deterministic extraction plus optional semantic vision |
| 3 | WhatsApp voice notes (see audio) | High | Low–medium | Natural input and easy user consent |
| 4 | Mac one-shot/low-frequency screen stills | Medium–high | Medium | Useful for dashboards; needs macOS permissions and a daemon |
| 5 | YouTube/TikTok transcript + sampled frames | Medium | Medium–high | Access, anti-bot, copyright, and frame sampling are variable |
| 6 | Continuous vision/live phone screen | Potentially high | High | Needs a dedicated app/integration, controls, bandwidth, and privacy UX |

### 2.3 Cost and buildability comparison

| Path | Free/low-cost buildability now | Pro-budget buildability | Caveats |
|---|---|---|---|
| Local OCR | Apple Vision framework on an Apple device; open-source PDF/DOC parsers on the Mac | Hosted document intelligence can add tables/layout | OCR extracts text; it is not semantic vision |
| Small hosted vision API | A GPT-4o-mini-style vision API or similar low-cost vision-capable API may be practical for occasional images | Higher-capability hosted vision, batching, storage, observability, and SLAs | API availability and cost change; do not hard-code a current model or price |
| Local open vision | LLaVA-family models in Docker are possible | GPU host or managed inference improves latency | A 2012 MacBook CPU may be too slow for interactive use and may lack supported acceleration; keep images small and use as an offline experiment |
| Desktop capture | Native `screencapture`, local OCR, and one-shot processing | Managed Mac agent, encrypted queue, and hosted vision | Screen Recording permission and secret exposure are operational risks |
| Video sampling | `ffmpeg`/local frame extraction plus captions where accessible | Hosted media pipeline and durable job queue | Login, anti-bot, terms, copyright, and storage constraints remain |

The low-cost design should prefer local OCR/local extraction and send only the minimized artifact or selected frames to a semantic vision service. Do not call local OCR “vision understanding.”

## 3. Audio, both directions

### 3.1 KYLA speaks (text to speech)

| Option | Role | Technical notes |
|---|---|---|
| `edge-tts` | Practical online baseline | Uses Microsoft's online Edge speech service; supports many voices and controls such as rate, volume, pitch, and SSML-like input. Availability, limits, service behavior, and commercial rights are not guaranteed to be unlimited; verify current terms before production. |
| Piper | Private/offline fallback | Local, low-resource neural TTS; choose a voice/model whose license permits the intended use. Voice/model licenses are separate concerns from the runtime. Good fit for a 2012 Mac for short responses, subject to model size and speed. |
| Coqui TTS options | Experimentation or a richer local/hosted tier | Model, dataset, runtime, license, and maintenance status vary. Pin versions and verify each model's license; do not assume all Coqui-derived models have the same rights or quality. |
| macOS `say` | Always-available fallback | Uses installed system voices and can play directly through the Mac. Quality and voice availability depend on macOS; it is a reliability fallback, not a portable voice contract. |

Baseline: use `edge-tts` for personality and quality when an online call is acceptable, and Piper for a private offline fallback. Keep a text response available if synthesis fails. Cache short, non-sensitive audio only when policy permits.

**Voice persona — “JARVIS meets Maddy-sass”:** calm butler + attitude. Output is concise, warm, dry/playful, and occasionally witty; never insulting, humiliating, manipulative, or overconfident. It must state uncertainty plainly, especially for trading. A personality layer may rewrite phrasing but cannot change facts, confidence, safety controls, or a trade decision.

Practical quality tiers:

- **Free/private:** Piper or `say` locally; no hosted speech cost, but fewer voices and more setup/model-license work.
- **Free/online baseline:** `edge-tts` may offer excellent usable voices, but it depends on an online Microsoft Edge service and is not a guaranteed unlimited/commercial API.
- **Paid/Pro:** a supported hosted TTS provider, higher availability, monitoring, and a licensed custom voice if needed. Prices and product availability should be checked at implementation time.

#### Delivery targets

- **WhatsApp:** generate an OGG/Opus voice note (or the adapter's supported audio format), attach it with the text transcript, and preserve a concise text fallback.
- **Mac playback:** play through the selected output device using `say` or a local audio player; do not interrupt active calls without a user setting.
- **3D dashboard:** use speech as an event with caption, waveform/activity state, and avatar mouth/gesture animation. Animation is presentation only; it must not imply confidence or live awareness.

### 3.2 KYLA hears (speech to text)

**WhatsApp voice notes:** download to a temporary file, validate MIME/duration, normalize audio, transcribe, retain timestamps/segments, and delete the original according to the short retention window. Reply with a transcript or ask for confirmation when it is ambiguous.

**Local transcription:** OpenAI Whisper in Docker is free to run locally. On a 2012 MacBook it will be CPU-bound and slow-ish, but short voice notes are feasible. `faster-whisper` uses CTranslate2 and can improve CPU throughput with a suitable quantized model and VAD; benchmark on the actual machine rather than assuming real-time performance. A small model is a latency/accuracy trade-off, not a promise of perfect transcription.

**Always-on Mac microphone design:** make it opt-in, show an unmistakable recording/listening indicator, keep audio in a ring buffer only if required, and discard audio that does not pass the wake-word gate. Require a system microphone permission for the actual process. Provide a push-to-talk hotkey/button as the default fallback and disable listening while sensitive windows or calls are active if configured.

**Wake word:** openWakeWord is a practical local option. Porcupine is an alternative with its own SDK, account, and license terms. Wake words produce false wakes and misses, especially with TV/radio, accents, noise, and speech that resembles the phrase. A wake event must not authorize a trade or external side effect; it only starts an interaction. Add a short confirmation/listening timeout and push-to-talk fallback.

## 4. The visual interface

### 4.1 Experience and rendering model

The interface remains an animated Kilimani penthouse with agent characters as already specced. “Holographic” on-screen reading should mean styled DOM overlays, panels, and highlights layered over the scene—not physical holograms. The dashboard can show price, positions, signals, data age, provenance, confidence, and rule state as animated cards. Use explicit stale-data badges; animation must never make old market data look live.

Include a screen-sleep idle ambient mode: pause expensive rendering, dim or switch to a static scene, stop nonessential polling, and wake on input or a configured event. Do not let ambient mode keep microphone or screen capture active without its separate consent state.

### 4.2 Three.js, react-three-fiber, DOM/CSS, and Astra

| Choice | Strength | 2012 Mac risk | Recommendation |
|---|---|---|---|
| Pure DOM/CSS animation | Lowest GPU/JS cost, accessible text, excellent data cards | Complex scenes become layout-heavy | Use for cards, reading overlays, tables, controls, and most motion |
| Three.js | Direct WebGL control for a lightweight hero scene | WebGL driver/GPU limits, heat, battery, scene complexity | Use only for a small scene with a 2D fallback |
| react-three-fiber | React composition for Three.js scenes | Adds React/render-loop overhead and another abstraction | Use if the existing app is React and the scene remains small |
| Astra free/pro | Astra is ambiguous; likely the WordPress theme and its free/pro plans, not a 3D engine | Not a WebGL rendering solution | Do not present Astra as a Three.js or 3D alternative; use only if a WordPress shell is actually needed |

Recommended hybrid: DOM/CSS for interface and live cards, light WebGL/Three.js only for the hero penthouse/characters, and a graceful 2D illustration/CSS fallback. Start with a static scene and add motion only after input and data flows work.

### 4.3 Performance safeguards

- Detect low-power/old hardware and default to 2D, reduced motion, low resolution, and a low frame rate.
- Pause WebGL when hidden or idle; cap device pixel ratio; avoid large textures, post-processing, shadows, particle systems, and unnecessary re-renders.
- Throttle price/chart polling independently from animation. Use CSS transitions for cards and virtualize long logs.
- Keep audio decoding and vision jobs off the render thread. Queue heavy work and show progress.
- Respect `prefers-reduced-motion`, provide a “lite mode,” and keep all important readings accessible as text.
- Instrument frame time, memory, queue latency, dropped frames, and Mac temperature/fan symptoms where possible. A crash-safe 2D dashboard is the acceptance baseline.

## 5. Three end-to-end multimodal flows

### Flow A — TradingView screenshot to rule-aware explanation

1. Mel sends a TradingView screenshot in WhatsApp.
2. Adapter validates type, strips unnecessary metadata, stores it temporarily, and assigns an artifact ID.
3. Local OCR extracts visible symbols, labels, prices, and indicator text; a vision step identifies chart regions and readable structure.
4. KYLA returns observations, pattern explanation, visible/missing inputs, uncertainty, and a check against SSS/BBB rules.
5. The response explicitly says **no trade execution**. Any live price, position, or news check is a separate permitted adapter call and must be timestamped.

Integrations may be staged or mocked until WhatsApp, market, position, news, and SSS/BBB rule adapters exist.

### Flow B — “KYLA what’s the market doing” by voice

1. Mel records a WhatsApp voice note or presses push-to-talk on the Mac.
2. Whisper/faster-whisper transcribes and returns segments/confidence; ambiguous symbols or time windows are confirmed.
3. A policy-controlled orchestrator checks only permitted positions, approved market data, and approved news sources, with freshness timestamps.
4. KYLA produces a concise answer, a chart/data panel with provenance and stale-data warnings, and a voice note using `edge-tts` or Piper.
5. No order is created. Any future execution requires an independent strategy result, explicit confirmation, and an auditable order gate.

Until data/news/WhatsApp adapters are present, the flow can use fixtures and visibly labeled mock data only.

### Flow C — TikTok link to evidence-based strategy summary

1. Mel pastes the TikTok URL in WhatsApp.
2. The link handler validates the URL, applies access/terms policy, and tries captions/transcript plus bounded sampled frames.
3. KYLA aligns spoken claims with frame timestamps, identifies missing or contradictory visual evidence, and summarizes the strategy.
4. It labels the result **USEFUL** or **SKIP** with evidence, assumptions, and confidence—not as financial advice or a promise.
5. If access is blocked, login-gated, anti-bot protected, or copyright/retention policy disallows retrieval, KYLA asks for an authorized upload or returns the partial transcript with the limitation.

## 6. Architecture and data flow

```text
iPhone / Mac UI
   |  WhatsApp text, image, document, video, voice note
   v
WhatsApp adapter -> validation + size/type limits -> temporary object store
                                      |
                 +--------------------+--------------------+
                 |                                         |
       local extractors                              optional semantic services
 OCR / PDF-DOC parser / ffmpeg / STT              vision / hosted STT-TTS
                 |                                         |
                 +--------------------+--------------------+
                                      v
             provenance + confidence + policy-aware orchestrator
                     |                 |                 |
              rule/data adapters    response composer   audit log
                     |                 |                 |
                     +---------- text / audio / panel --+
                                      |
                              WhatsApp / web dashboard / Mac audio
```

For the Mac capture path, `screencapture` feeds the temporary object store, then follows the same extractor/orchestrator route. For all inputs, record an artifact ID, source type, source timestamp if known, processing timestamp, transformations, extractor/model versions, confidence, and deletion deadline. Separate raw media, derived text, embeddings, and logs so a deletion request can remove all associated records.

### Storage and trust controls

- Encrypt transport and storage where available; use a local encrypted directory with restrictive permissions for the short-lived work area.
- Set a default deletion deadline for raw attachments and screen frames (for example, after processing or within a short operational window); make the policy configurable and document any retained derivatives. Do not retain by default for model training.
- Redact API keys, passwords, wallet/seed phrases, personal identifiers, and private contact details before external calls where possible. Never put secrets into prompts or logs.
- Treat PDFs, media, captions, webpages, and model outputs as untrusted data. Defend against prompt injection in documents and transcripts; quoted instructions from content are not KYLA instructions.
- Keep provenance and confidence with every conclusion. Distinguish direct observation, OCR, transcription, inference, external data, and user-provided claims.
- Apply rate limits, maximum duration/frame/page counts, MIME validation, decompression-bomb protection, sandboxed parsers, and job timeouts.
- Log access and decisions without logging raw sensitive media by default. Log confirmation events, policy decisions, adapter calls, data timestamps, and the final trade decision state.

### Trading safety controls

1. **No autonomous trade from media:** an image/audio/video interpretation is advisory only.
2. **Fresh data requirement:** live price, position, and news claims need an approved adapter and timestamp; screenshot values are not live values.
3. **Rule gate:** SSS/BBB evaluation must use explicit structured inputs and report unknowns; missing values fail closed.
4. **Confirmation gate:** a separate UI/WhatsApp confirmation states instrument, side, quantity, order type, price assumptions, data age, and risk checks before any execution adapter is called.
5. **Auditability:** store the input artifact ID, extracted evidence, model/version, rule result, user confirmation, and adapter response.
6. **Fail safe:** uncertainty, stale data, permission errors, provider errors, or suspicious content produce a non-actionable answer and request clarification.

## 7. Prioritized build roadmap

Effort estimates are for one developer familiar with the existing stack, not guaranteed calendar time. They intentionally avoid assuming the exact Mac model or RAM limit.

| Priority | Deliverable | Estimate | Dependencies | Where it runs | Cost class |
|---|---|---:|---|---|---|
| P0 | WhatsApp attachment intake, validation, temporary storage/deletion, screenshots/photos, text reply | 2–4 days | WhatsApp adapter/auth, existing service | iPhone sends; Mac/server processes | Cheap/free plus any WhatsApp/provider fees |
| P0 | Local OCR + PDF/DOC text extraction and page rendering | 2–5 days | Sandboxed parsers, OCR library | Fine on the Mac for bounded documents; phone is transport | Cheap/free |
| P0 | Whisper/faster-whisper voice-note transcription and text fallback | 2–4 days | Docker, ffmpeg, audio limits | Phone records; short notes run on 2012 Mac, slower on CPU | Free local; paid hosted STT optional |
| P0 | Provenance, confidence, prompt-injection defense, retention, redaction, no-trade gate | 2–4 days | All input jobs | Mac/service; policy applies everywhere | Cheap/free engineering |
| P1 | Hosted low-cost vision step for selected screenshots/pages; fixture-based SSS/BBB explanation | 3–7 days | API key, adapter, cost/rate limits | Mac orchestrates; external vision does inference | Paid API/Pro budget; API cost changes |
| P1 | `edge-tts` speech replies plus Piper/`say` fallback and WhatsApp audio packaging | 2–4 days | TTS service or local models | Mac generates; phone receives | Free/low-cost baseline; hosted tier optional |
| P1 | Mac `screencapture` one-shot and 10–30 second low-frequency mode | 3–6 days | Screen Recording permission, launch agent, window allowlist | 2012 Mac only; iPhone cannot supply system live share | Cheap/free; hosted vision optional |
| P1 | Web dashboard: DOM/CSS cards, captions, data age, reduced-motion/lite mode | 3–7 days | Existing frontend/data fixtures | Should run in phone browser and Mac browser; use 2D first | Cheap/free |
| P2 | YouTube/TikTok transcript + frame sampling with access/copyright handling | 4–10 days | Legal/terms review, ffmpeg, platform adapters | Mac/service; phone only submits link | Cheap tooling; hosted queue/storage may be paid |
| P2 | Light Three.js/react-three-fiber penthouse hero with 2D fallback | 5–12 days | Existing frontend, performance tests | 2012 Mac only in lite mode; phone gets 2D/mobile view | Cheap/free libraries; extra design time |
| P2 | Opt-in always-on Mac microphone, wake word, ring buffer, tuning | 5–10 days | Mic permission, openWakeWord/alternative, UX | Mac; not an iPhone system capability | Free local; alternative SDK may be paid |
| P2 | Provider-grade vision/STT/TTS, hosted workers, monitoring, encrypted durable queue | 1–3 weeks | Adapter contracts, budget, privacy review | Hosted service plus Mac/phone clients | Pro budget |

**Hardware order:** if the 2012 Mac still has a hard disk drive, upgrade to an SSD first. Then upgrade RAM to the maximum supported by the exact model, after checking its documented limit; the exact model and current RAM are unknown here. Do these before expecting local models or a 3D scene to be pleasant. Do not buy hardware based on an assumed Mac model. A Pro budget is most useful after P0: hosted vision, speech, queueing, monitoring, and reliable adapters usually improve capability more than prematurely attempting a large local model.

**Device division:** the iPhone is primarily capture, WhatsApp transport, playback, and a browser dashboard. The Mac handles extraction, Docker, local OCR/STT/TTS, `screencapture`, orchestration, and optional WebGL. Heavy vision, hosted services, and production queues belong on a Pro-budget service only when latency, privacy, or reliability justifies them.

## 8. Acceptance criteria and open integration work

The first shippable slice is complete when a user can send a screenshot, PDF/DOC, or voice note through WhatsApp; receive a response that distinguishes extraction from inference; see a confidence/provenance statement; and verify that raw media is deleted on schedule. Failure must be visible and recoverable.

Open work that is intentionally not hidden by this specification:

- Select and authenticate the WhatsApp adapter and define supported media limits.
- Confirm the exact 2012 Mac model, macOS version, storage, RAM, Docker support, and available permissions.
- Implement market, positions, news, SSS/BBB, and order adapters with a separate confirmation gate.
- Decide data residency, retention duration, consent wording, and whether any provider may retain submitted content.
- Benchmark Whisper/faster-whisper, Piper, OCR, and the browser scene on the actual Mac.
- Choose a hosted vision/STT/TTS provider only after current availability, API terms, and cost are checked.
- Define a test corpus of screenshots, noisy voice notes, scans, charts, and hostile documents; measure false claims, false wakes, latency, and deletion behavior.

## What KYLA becomes
A consent-driven multimodal assistant for Mel's phone-and-Mac workflow.
A reader of screenshots, documents, links, screens, photos, and voice notes.
A calm voice and visual dashboard with evidence, provenance, and uncertainty.
A lightweight Kilimani interface that degrades gracefully on old hardware.
A trading-aware copilot that never turns ambiguous media into an autonomous trade.

## Reference URLs

- https://github.com/openai/whisper
- https://openai.com/index/whisper/
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/rhasspy/piper
- https://github.com/dscripka/openWakeWord
- https://github.com/dscripka/openWakeWord/blob/main/LICENSE
- https://developer.apple.com/documentation/vision/recognizing-text-in-images
- https://developer.apple.com/documentation/vision/locating-and-displaying-recognized-text
- https://threejs.org
- https://github.com/mrdoob/three.js
- https://r3f.docs.pmnd.rs
- https://github.com/pmndrs/react-three-fiber
- https://wpastra.com/
- https://wpastra.com/astra-free-vs-pro/
- https://github.com/rany2/edge-tts
- https://github.com/coqui-ai/TTS
