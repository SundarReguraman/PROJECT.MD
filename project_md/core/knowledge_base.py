"""The trap knowledge base: the architectural dead ends beginners walk into most.

Each trap explains WHY the naive approach fails in plain English and mandates
the modern replacement (CLAUDE.md rule 3). Patterns are case-insensitive
regexes; see ``Trap`` for how ``idea_patterns`` and ``anti_patterns`` differ.

To add a trap: append to ``TRAPS`` with the next id in its category. The
integrity tests in ``tests/test_knowledge_base.py`` enforce unique ids and
valid regexes.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from project_md.core.models import Category, Severity, Trap, TrapWarning

# Building blocks for OCR-001: a surface people write on by hand, and turning it into text.
# "Uber for X"-style service marketplaces: live location, bookings, payments, payouts.
SERVICE_MARKETPLACE = r"\b(?:uber|lyft|doordash|deliveroo|taskrabbit|rover|fiverr|airbnb) for\b|\bon[- ]demand\b|\btwo[- ]sided\b"

HANDWRITTEN_SURFACE = r"\b(?:whiteboards?|chalkboards?|blackboards?|notebooks?|sticky notes?|post-?its?|lecture notes|class notes|scanned notes)\b"
TO_TEXT = r"(?:\b(?:into|to) (?:digital |editable |searchable )?text\b|\btranscri\w*|\bdigiti[sz]\w*|\bocr\b|\bextract\w* (?:the )?text\b)"

TRAPS: Tuple[Trap, ...] = (
    # ── OCR ──────────────────────────────────────────────────────────────
    Trap(
        id="OCR-001",
        category=Category.OCR,
        severity=Severity.CRITICAL,
        title="Handwriting recognition with OpenCV or basic Tesseract",
        idea_patterns=(
            r"hand[- ]?writ\w*", r"\bcursive\b", r"\bwritten by hand\b", r"\bscribbl\w*",
            # Doctors' notes/prescriptions in either word order.
            r"\bdoctor\w*['\u2019]?s?\b.*\b(?:notes?|prescriptions?|writing)\b",
            r"\b(?:notes?|prescriptions?)\b.*\bdoctors?\b",
            # Reading/digitising prescriptions (not merely managing refills).
            r"\b(?:read|scan|digiti[sz]|transcrib|photo|ocr|extract)\w*\b.*\bprescriptions?\b",
            r"\bprescriptions?\b.*\b(?:read|scan|digiti[sz]|transcrib|ocr|extract)\w*",
            # Surfaces people write on by hand, turned into text.
            HANDWRITTEN_SURFACE + r".*" + TO_TEXT,
            TO_TEXT + r".*" + HANDWRITTEN_SURFACE,
        ),
        anti_patterns=(r"\bopen ?cv\b", r"\bcv2\b", r"\btesseract\b", r"\bcontours?\b", r"\bthreshold\w*"),
        trap="OpenCV contours/thresholding or stock Tesseract to read handwriting",
        why_it_fails=(
            "OpenCV is an image-filtering toolkit: it can find blobs and edges, but it has no idea "
            "what a letter is. Tesseract was trained on printed fonts and collapses on joined-up, "
            "slanted, inconsistent handwriting. You will write thousands of lines of pixel hacks "
            "that work on one sample and fail on the next."
        ),
        recommended=(
            "TrOCR (Hugging Face; run offline via ONNX Runtime)",
            "Donut or a vision-language model for full pages",
            "Google Cloud Vision / AWS Textract if cloud is acceptable",
        ),
    ),
    Trap(
        id="OCR-002",
        category=Category.OCR,
        severity=Severity.WARNING,
        title="Parsing invoices, receipts or forms with regex over raw OCR text",
        idea_patterns=(r"\binvoices?\b", r"\breceipts?\b", r"\bforms?\b.*\b(?:extract|scan|parse)", r"\b(?:extract|scan|parse)\w*\b.*\bforms?\b", r"\bexpense"),
        anti_patterns=(r"\bregex\w*", r"\bregular expressions?\b", r"\bpytesseract\b"),
        trap="Flattening a document to plain text with OCR, then regex-matching fields",
        why_it_fails=(
            "OCR throws away the layout, so 'Total' and its amount end up on different lines, or "
            "in the wrong order, depending on the scan. Every new vendor template breaks your "
            "regexes and you end up maintaining one rule set per supplier."
        ),
        recommended=(
            "Layout-aware extraction: Azure Document Intelligence, AWS Textract AnalyzeExpense",
            "Donut or LayoutLMv3 for self-hosted extraction",
            "A vision-capable LLM with a strict JSON output schema",
        ),
    ),
    Trap(
        id="OCR-003",
        category=Category.OCR,
        severity=Severity.WARNING,
        title="Running OCR on PDFs that already contain text",
        idea_patterns=(r"\bpdfs?\b",),
        anti_patterns=(r"\bocr\b", r"\btesseract\b", r"\bpdf2image\b"),
        trap="Rasterising every PDF page to an image and OCR-ing it",
        why_it_fails=(
            "Most PDFs made by software already contain the exact text. Converting them to images "
            "and OCR-ing them is 100x slower and introduces typos into text that was perfect."
        ),
        recommended=(
            "Read the text layer first with pypdf or pdfplumber",
            "Fall back to OCR only for pages with no extractable text (true scans)",
        ),
    ),
    # ── Computer vision ──────────────────────────────────────────────────
    Trap(
        id="CV-001",
        category=Category.COMPUTER_VISION,
        severity=Severity.CRITICAL,
        title="Object detection with Haar cascades or hand-tuned OpenCV",
        idea_patterns=(r"\bdetect\w*\b.*\b(?:objects?|people|cars?|vehicles?|animals?|defects?|items?)\b", r"\bobject detection\b", r"\bcount\w*\b.*\b(?:people|cars?|objects?)\b", r"\bsecurity camera\b"),
        anti_patterns=(r"\bhaar\b", r"\bcascade\w*\b", r"\bopen ?cv\b", r"\bcv2\b", r"\bcolou?r (?:mask|threshold)\w*"),
        trap="Haar cascades, colour masks and contour rules to find objects",
        why_it_fails=(
            "Hand-written detection rules depend on lighting, angle and background. They pass "
            "on your test photo and fail the moment the camera moves or the sun sets. Modern "
            "detectors learn these variations from data instead."
        ),
        recommended=(
            "YOLO (Ultralytics) or RT-DETR, fine-tuned on a few hundred labelled images",
            "MediaPipe for people, hands and faces",
            "Export to ONNX for fast CPU/edge inference",
        ),
    ),
    Trap(
        id="CV-002",
        category=Category.COMPUTER_VISION,
        severity=Severity.CRITICAL,
        title="Face recognition by comparing pixels or histograms",
        idea_patterns=(r"\bface (?:recognition|id|unlock|match\w*)\b", r"\brecogni[sz]e\w*\b.*\bfaces?\b", r"\battendance\b.*\bfaces?\b"),
        anti_patterns=(r"\bpixel\w*\b", r"\bhistograms?\b", r"\blbph\b", r"\beigenfaces?\b", r"\btemplate match\w*"),
        trap="Pixel difference, histograms or LBPH/Eigenfaces to identify people",
        why_it_fails=(
            "The same person photographed twice differs more pixel-for-pixel than two different "
            "people in the same pose and lighting. These methods give false matches that are both "
            "embarrassing and a security hole."
        ),
        recommended=(
            "Face embeddings: InsightFace/ArcFace or the face_recognition library",
            "Compare embeddings with cosine distance against an enrolled set",
            "Add liveness detection if it gates access to anything",
        ),
    ),
    Trap(
        id="CV-003",
        category=Category.COMPUTER_VISION,
        severity=Severity.WARNING,
        title="Running a heavy model on every video frame in a Python loop",
        idea_patterns=(r"\b(?:live|real[- ]?time)\b.*\b(?:video|camera|webcam|stream)\b", r"\b(?:video|camera|webcam)\b.*\b(?:live|real[- ]?time)\b", r"\bcctv\b"),
        anti_patterns=(r"\bevery frame\b", r"\bframe by frame\b", r"\bupload\w* frames?\b"),
        trap="Full-size model inference on every frame, or posting frames to an HTTP API",
        why_it_fails=(
            "A 30 fps camera gives you 33 ms per frame. A full PyTorch model on CPU takes several "
            "times that, so the video lags further and further behind reality. Sending frames "
            "over HTTP adds network latency on top."
        ),
        recommended=(
            "Skip frames and track between detections (e.g. ByteTrack)",
            "Small models exported to ONNX Runtime / TensorRT / Core ML",
            "WebRTC for browser video instead of HTTP frame uploads",
        ),
    ),
    # ── Auth ─────────────────────────────────────────────────────────────
    Trap(
        id="AUTH-001",
        category=Category.AUTH,
        severity=Severity.CRITICAL,
        title="Storing passwords yourself with plain text or fast hashes",
        idea_patterns=(r"\blog ?in\b", r"\bsign ?(?:up|in)\b", r"\baccounts?\b", r"\bpasswords?\b", r"\busers? register\w*"),
        anti_patterns=(r"\bmd5\b", r"\bsha-?1\b", r"\bsha-?256\b", r"\bplain ?text passwords?\b", r"\bstore\w* (?:the )?passwords?\b"),
        trap="Saving passwords as plain text or hashing them with MD5/SHA",
        why_it_fails=(
            "When (not if) the database leaks, plain text passwords are instantly usable and "
            "MD5/SHA hashes are cracked at billions of guesses per second on a gaming GPU. "
            "Your users reuse those passwords on their email and bank."
        ),
        recommended=(
            "Managed auth: Supabase Auth, Clerk, Auth0, Firebase Auth",
            "If self-hosting: Argon2id (argon2-cffi) or bcrypt, never a general-purpose hash",
        ),
    ),
    Trap(
        id="AUTH-002",
        category=Category.AUTH,
        severity=Severity.WARNING,
        title="Long-lived JWTs in localStorage for browser sessions",
        idea_patterns=(r"\bweb ?app\b.*\b(?:log ?in|accounts?|auth\w*)\b", r"\b(?:log ?in|accounts?|auth\w*)\b.*\bweb ?app\b", r"\bjwt\b"),
        anti_patterns=(r"\blocal ?storage\b", r"\bjwt\b.*\bnever expire\w*", r"\bno expir\w*"),
        trap="Putting a never-expiring JWT in localStorage",
        why_it_fails=(
            "Any script on the page, including a compromised npm package or an XSS bug, can read "
            "localStorage and steal the token. A JWT cannot be revoked, so a stolen one works "
            "until it expires, which for 'never' means forever."
        ),
        recommended=(
            "Session cookies marked httpOnly, Secure, SameSite",
            "Short-lived access tokens plus rotating refresh tokens",
            "Or let a managed auth provider handle sessions",
        ),
    ),
    Trap(
        id="AUTH-003",
        category=Category.AUTH,
        severity=Severity.WARNING,
        title="Hand-rolling OAuth / social login",
        idea_patterns=(r"\b(?:google|github|apple|facebook|microsoft) (?:log ?in|sign[- ]?in|auth\w*)\b", r"\boauth\w*\b", r"\bsocial log ?in\b", r"\bsso\b"),
        anti_patterns=(r"\b(?:from scratch|by hand|manually|my own)\b.*\boauth\b", r"\boauth\b.*\b(?:from scratch|by hand|manually)\b"),
        trap="Implementing the OAuth redirect/token dance by hand",
        why_it_fails=(
            "OAuth has subtle security steps (state, PKCE, nonce, token validation) that are easy "
            "to skip and invisible when skipped. The login 'works' while being open to account "
            "takeover."
        ),
        recommended=(
            "Auth.js (NextAuth), Authlib, or Passport strategies",
            "Managed providers: Clerk, Supabase Auth, Auth0, Firebase Auth",
        ),
    ),
    # ── Database ─────────────────────────────────────────────────────────
    Trap(
        id="DB-001",
        category=Category.DATABASE,
        severity=Severity.WARNING,
        title="Using JSON or CSV files as the application database",
        idea_patterns=(r"\b(?:store|save|track|manage)\w*\b", r"\binventory\b", r"\bbookings?\b", r"\bdashboard\b"),
        anti_patterns=(r"\bjson files?\b", r"\bcsv files?\b", r"\bsave\w* (?:it |them )?to (?:a )?(?:json|csv|text) files?\b", r"\bexcel (?:as|file)\b"),
        trap="Reading and rewriting a JSON/CSV file on every change",
        why_it_fails=(
            "Two requests writing at the same moment silently overwrite each other, a crash "
            "mid-write corrupts the whole file, and every lookup reads everything. It feels "
            "simpler for a day and costs you your data within a month."
        ),
        recommended=(
            "SQLite for single-machine or offline apps (built into Python)",
            "PostgreSQL (e.g. via Supabase or Neon) for multi-user web apps",
        ),
    ),
    Trap(
        id="DB-002",
        category=Category.DATABASE,
        severity=Severity.WARNING,
        title="MongoDB/NoSQL for highly relational data",
        idea_patterns=(SERVICE_MARKETPLACE, r"\be-?commerce\b", r"\bshop\b", r"\bstore front\b", r"\bbookings?\b", r"\breservations?\b", r"\binventory\b", r"\b(?:orders?|payments?|invoices?)\b", r"\bmarketplace\b"),
        anti_patterns=(r"\bmongo\w*\b", r"\bnosql\b", r"\bfirestore\b", r"\bdynamo\w*\b"),
        trap="A document database for orders, users, products and payments",
        why_it_fails=(
            "Orders reference users, products and payments. Without joins and multi-row "
            "transactions you either duplicate data (and it drifts out of sync) or stitch it "
            "together in application code. Stock counts go negative under concurrent checkouts."
        ),
        recommended=(
            "PostgreSQL with foreign keys and transactions",
            "Use a JSONB column for the genuinely schemaless parts",
        ),
    ),
    Trap(
        id="DB-003",
        category=Category.DATABASE,
        severity=Severity.CRITICAL,
        title="Storing money as floating-point numbers",
        idea_patterns=(r"\b(?:payments?|prices?|pricing|money|budget\w*|expenses?|invoices?|wallet|billing|accounting|finance\w*|salary|salaries|checkout)\b",),
        anti_patterns=(r"\bfloats?\b", r"\bdouble\b", r"\breal column\b"),
        trap="Using float/double for prices, balances and totals",
        why_it_fails=(
            "Floats cannot represent 0.10 exactly, so 0.1 + 0.2 = 0.30000000000000004. Totals "
            "drift by fractions of a cent, reports stop reconciling, and refunds come out wrong."
        ),
        recommended=(
            "Integer minor units (store cents as an int)",
            "Python decimal.Decimal / SQL NUMERIC(12,2)",
            "Stripe or another payment provider for the actual money movement",
        ),
    ),
    Trap(
        id="DB-004",
        category=Category.DATABASE,
        severity=Severity.WARNING,
        title="Microservices and multiple databases for an MVP",
        idea_patterns=(r"\bmvp\b", r"\bhackathon\b", r"\bprototype\b", r"\bside project\b", r"\bweekend\b", r"\bstartup\b"),
        anti_patterns=(r"\bmicro-?services?\b", r"\bkubernetes\b", r"\bk8s\b", r"\bservice mesh\b", r"\bdatabase per service\b"),
        trap="Splitting a new product into many services with separate databases",
        why_it_fails=(
            "You don't yet know where the real boundaries are, so you guess wrong and pay for it "
            "in network calls, distributed bugs and deployment plumbing instead of features. "
            "Teams far larger than yours start as a monolith."
        ),
        recommended=(
            "A modular monolith: one deployable, clear internal modules",
            "One database (SQLite or PostgreSQL)",
            "Extract a service only when a module has a proven, separate scaling need",
        ),
    ),
    # ── Queues & background work ─────────────────────────────────────────
    Trap(
        id="QUEUE-001",
        category=Category.QUEUE,
        severity=Severity.WARNING,
        title="Doing slow work inside the HTTP request",
        idea_patterns=(r"\b(?:transcod\w*|render\w*|convert\w*)\b.*\b(?:video|audio|files?)\b", r"\b(?:send|bulk)\b.*\bemails?\b", r"\bgenerate\w*\b.*\b(?:reports?|pdfs?|videos?)\b", r"\btranscri\w*\b.*\b(?:audio|video|podcasts?|meetings?|calls?|recordings?)\b", r"\bbatch\b"),
        anti_patterns=(r"\bin the (?:request|endpoint|route|handler)\b", r"\bwait\w* for (?:it|the \w+) to finish\b", r"\bsynchronous\w*\b"),
        trap="Running transcoding, AI inference or bulk email inside the web request",
        why_it_fails=(
            "Browsers, proxies and hosting platforms time requests out after 30-100 seconds. "
            "Long jobs get killed half-way, users click retry, and now the job runs twice."
        ),
        recommended=(
            "Return immediately with a job id; process in a background worker",
            "Python: RQ, Dramatiq or Celery. Node: BullMQ. Or a managed queue (SQS, Cloud Tasks)",
            "Push progress back via polling a status endpoint, SSE or WebSockets",
        ),
    ),
    Trap(
        id="QUEUE-002",
        category=Category.QUEUE,
        severity=Severity.INFO,
        title="Kafka or RabbitMQ clusters for a small app",
        idea_patterns=(r"\bqueues?\b", r"\bbackground (?:jobs?|tasks?|workers?)\b", r"\bevents?\b.*\bprocess\w*\b", r"\bnotifications?\b"),
        anti_patterns=(r"\bkafka\b", r"\brabbit ?mq\b", r"\bpulsar\b"),
        trap="Operating a distributed streaming platform for a few jobs per second",
        why_it_fails=(
            "Kafka is built for millions of events per second across many teams. For a small app "
            "it is days of setup, a cluster to babysit and a monthly bill, for load a single "
            "Redis or Postgres table handles without noticing."
        ),
        recommended=(
            "Redis + RQ/BullMQ",
            "A Postgres-backed queue (e.g. pgmq, Procrastinate, or SELECT ... FOR UPDATE SKIP LOCKED)",
            "Managed: AWS SQS, Google Cloud Tasks",
        ),
    ),
    # ── Concurrency ──────────────────────────────────────────────────────
    Trap(
        id="CONC-001",
        category=Category.CONCURRENCY,
        severity=Severity.WARNING,
        title="A synchronous requests loop for heavy I/O",
        idea_patterns=(r"\b(?:thousands|hundreds|millions|lots) of (?:urls?|sites?|websites?|pages?|apis?|requests?|endpoints?)\b", r"\bmonitor\w*\b.*\b(?:websites?|urls?|uptime|prices?)\b", r"\bcrawl\w*\b"),
        anti_patterns=(r"\brequests\.get\b", r"\bfor (?:each|every) (?:url|site|page)\b", r"\bpython requests\b"),
        trap="Calling requests.get() one URL at a time in a for-loop",
        why_it_fails=(
            "Each request spends ~99% of its time waiting on the network. Done one after another, "
            "10,000 URLs at 500 ms each take over an hour; done concurrently they take a minute."
        ),
        recommended=(
            "asyncio + httpx (or aiohttp) with a semaphore to cap concurrency",
            "Or a runtime with cheap concurrency: Go goroutines, Node.js",
        ),
    ),
    Trap(
        id="CONC-002",
        category=Category.CONCURRENCY,
        severity=Severity.WARNING,
        title="Python threads to speed up CPU-heavy work",
        idea_patterns=(r"\b(?:simulat\w*|number crunch\w*|image processing|process\w* (?:large|big|huge) (?:files?|datasets?|data)|heavy computation)\b", r"\bparallel\w*\b"),
        anti_patterns=(r"\bthreads?\b", r"\bthreading\b", r"\bThreadPoolExecutor\b"),
        trap="Using threading to parallelise CPU-bound Python code",
        why_it_fails=(
            "CPython's Global Interpreter Lock lets only one thread run Python bytecode at a time. "
            "CPU-bound code on 8 threads runs no faster than on 1, and sometimes slower."
        ),
        recommended=(
            "multiprocessing / concurrent.futures.ProcessPoolExecutor",
            "Vectorise with NumPy/Polars, which release the GIL in native code",
        ),
    ),
    # ── Real-time ────────────────────────────────────────────────────────
    Trap(
        id="RT-001",
        category=Category.REALTIME,
        severity=Severity.CRITICAL,
        title="HTTP polling for chat and live updates",
        idea_patterns=(r"\bchat\w*\b", r"\bmessag\w*\b", r"\blive (?:updates?|feed|scores?|tracking|dashboard|notifications?)\b", r"\breal[- ]?time\b", r"\bmultiplayer\b", r"\binstant\w*\b"),
        anti_patterns=(r"\bpoll\w*\b", r"\bsetInterval\b", r"\brefresh\w* every\b", r"\bevery (?:\d+ )?seconds?\b"),
        trap="Clients asking the server 'anything new?' every second",
        why_it_fails=(
            "1,000 users polling each second is 86 million mostly-empty requests a day. Messages "
            "still arrive up to a full interval late, and your server bill scales with idle users, "
            "not with actual activity."
        ),
        recommended=(
            "WebSockets (Socket.IO, FastAPI WebSockets) for two-way traffic",
            "Server-Sent Events for one-way server-to-client updates",
            "Managed realtime: Supabase Realtime, Ably, Pusher, Firebase",
        ),
    ),
    Trap(
        id="RT-002",
        category=Category.REALTIME,
        severity=Severity.CRITICAL,
        title="Collaborative editing with last-write-wins",
        idea_patterns=(r"\bcollaborat\w*\b", r"\bgoogle docs\b", r"\bshared (?:docs?|documents?|whiteboard|canvas|notes?|editor)\b", r"\bmulti-?user edit\w*\b", r"\bco-?edit\w*\b",
                       # A whiteboard is only a sync problem when people draw on it together.
                       r"\b(?:shared|collaborative|multiplayer|real[- ]?time|team)\b.*\bwhiteboards?\b",
                       r"\bwhiteboards?\b.*\b(?:together|collaborat\w*|multiplayer|real[- ]?time|shared)\b"),
        anti_patterns=(r"\blast[- ]write[- ]wins\b", r"\bsave the whole (?:doc|document)\b", r"\boverwrite\w*\b", r"\block\w* the (?:doc|document|file)\b"),
        trap="Each client saving the whole document, newest save wins",
        why_it_fails=(
            "Two people typing at once each save their copy; whichever lands second silently "
            "erases the other person's work. Locking the document instead makes it single-user."
        ),
        recommended=(
            "CRDTs: Yjs or Automerge (they merge concurrent edits automatically)",
            "Hosted sync: Liveblocks, PartyKit, y-websocket",
        ),
    ),
    # ── AI / ML ──────────────────────────────────────────────────────────
    Trap(
        id="AI-001",
        category=Category.AI_ML,
        severity=Severity.WARNING,
        title="Shipping full PyTorch models inside desktop/mobile/offline apps",
        idea_patterns=(r"\boffline\b", r"\bon[- ]device\b", r"\blocal(?:ly)?\b.*\b(?:ai|model|llm|transcri\w*|inference)\b", r"\belectron\b", r"\b(?:mobile|desktop|android|ios|iphone) app\b.*\b(?:ai|model|ml|transcri\w*|recogni\w*)\b", r"\braspberry pi\b"),
        anti_patterns=(r"\bpytorch\b", r"\btorch\b", r"\btensorflow\b", r"\btransformers\b"),
        trap="Bundling PyTorch/TensorFlow + Python runtime into an end-user app",
        why_it_fails=(
            "PyTorch alone is 700 MB-2 GB, needs a matching Python install, and is slow on CPUs "
            "without tuning. Your installer becomes gigabytes and cold start takes tens of seconds."
        ),
        recommended=(
            "Export to ONNX and run with ONNX Runtime",
            "whisper.cpp for speech, llama.cpp / Ollama for local LLMs",
            "Core ML (Apple), TensorFlow Lite / LiteRT (Android)",
        ),
    ),
    Trap(
        id="AI-002",
        category=Category.AI_ML,
        severity=Severity.CRITICAL,
        title="Training a model from scratch for a solved problem",
        idea_patterns=(r"\bchat ?bot\b", r"\bsentiment\b", r"\bspeech[- ]to[- ]text\b", r"\btranscri\w*\b.*\b(?:audio|speech|voice|podcasts?|meetings?|calls?|recordings?)\b", r"\btranslat\w*\b", r"\bsummari[sz]\w*\b", r"\bclassif\w*\b", r"\brecommend\w*\b.*\b(?:ai|ml)\b", r"\bai\b"),
        anti_patterns=(r"\btrain\w* (?:my own|our own|a|the) (?:\w+ )?(?:model|network|llm|neural net\w*)\b", r"\bfrom scratch\b", r"\bbuild\w* (?:my own|our own|an?) (?:llm|language model|neural network)\b"),
        trap="Collecting data and training a neural network from zero",
        why_it_fails=(
            "State-of-the-art models were trained on millions of examples with months of GPU time. "
            "With a few thousand examples yours will be far worse, and you'll spend weeks on "
            "training infrastructure instead of your product."
        ),
        recommended=(
            "Use a pretrained model or API first (Claude/GPT for text, Whisper for speech)",
            "Fine-tune a small pretrained model only if the API measurably falls short",
        ),
    ),
    Trap(
        id="AI-003",
        category=Category.AI_ML,
        severity=Severity.WARNING,
        title="Stuffing entire document collections into an LLM prompt",
        idea_patterns=(r"\bchat with (?:my |your |our )?(?:docs?|documents?|pdfs?|files?|notes?|knowledge base)\b", r"\bask questions? (?:about|over|on) (?:my |our )?(?:docs?|documents?|pdfs?|files?|notes?)\b", r"\bknowledge base\b", r"\bq ?& ?a\b.*\b(?:docs?|documents?)\b", r"\brag\b"),
        anti_patterns=(r"\b(?:send|paste|put|pass)\w* (?:all|every|the whole|the entire)\b.*\b(?:into|to|in) the (?:prompt|llm|context)\b", r"\bwhole (?:pdf|document|corpus)\b"),
        trap="Pasting every document into the prompt on every question",
        why_it_fails=(
            "Collections quickly exceed the context window, every question pays for every token "
            "of every document, and answers get worse as the relevant paragraph is buried in "
            "irrelevant text."
        ),
        recommended=(
            "Retrieval-augmented generation: chunk, embed, retrieve top-k, then prompt",
            "Hybrid search (keyword + vector) for better recall",
            "Cite the retrieved chunks in the answer",
        ),
    ),
    # ── Search ───────────────────────────────────────────────────────────
    Trap(
        id="SEARCH-001",
        category=Category.SEARCH,
        severity=Severity.INFO,
        title="Distributed vector databases for a small corpus",
        idea_patterns=(r"\bsemantic search\b", r"\bvector\w*\b", r"\bembeddings?\b", r"\bsimilar\w*\b.*\b(?:search|documents?|items?|products?)\b", r"\brag\b"),
        anti_patterns=(r"\bmilvus\b", r"\bpinecone\b", r"\bweaviate\b", r"\bqdrant cluster\b", r"\belasticsearch\b"),
        trap="Standing up Milvus/Pinecone/Weaviate for a few thousand documents",
        why_it_fails=(
            "Under ~1 million vectors, a brute-force or in-process index answers in milliseconds. "
            "A separate vector service adds a network hop, a bill, another credential and "
            "sync bugs between it and your main database."
        ),
        recommended=(
            "sqlite-vec or Chroma in-process",
            "pgvector inside the Postgres you already have",
        ),
    ),
    Trap(
        id="SEARCH-002",
        category=Category.SEARCH,
        severity=Severity.WARNING,
        title="Full-text search with SQL LIKE '%term%'",
        idea_patterns=(r"\bsearch\w*\b", r"\bfind\w*\b.*\b(?:articles?|posts?|products?|recipes?|notes?|documents?)\b"),
        anti_patterns=(r"\blike ['\"]?%", r"\blike operator\b", r"\bsql like\b", r"\bcontains\(\b"),
        trap="WHERE title LIKE '%query%' as the search feature",
        why_it_fails=(
            "A leading wildcard can't use an index, so every search scans every row. It also "
            "can't rank results, handle typos, or match 'running' to 'run'."
        ),
        recommended=(
            "SQLite FTS5 or PostgreSQL full-text search (tsvector)",
            "Meilisearch or Typesense for typo-tolerant, instant search",
        ),
    ),
    # ── Scraping ─────────────────────────────────────────────────────────
    Trap(
        id="SCRAPE-001",
        category=Category.SCRAPING,
        severity=Severity.WARNING,
        title="Scraping JavaScript-rendered sites with requests + BeautifulSoup",
        idea_patterns=(r"\bscrap\w*\b", r"\bcrawl\w*\b", r"\bprice (?:tracker|monitor\w*|comparison)\b", r"\bpull data from (?:a |the )?(?:website|site)\b"),
        anti_patterns=(r"\bbeautiful ?soup\b", r"\bbs4\b", r"\brequests\b", r"\burllib\b"),
        trap="Fetching raw HTML and parsing it, on sites that build the page in JavaScript",
        why_it_fails=(
            "Modern sites send an almost-empty HTML shell and fill it in with JavaScript. "
            "requests never runs that JavaScript, so the data you want simply isn't in the "
            "response, and the selectors break on every redesign."
        ),
        recommended=(
            "Check for an official API or the site's own JSON endpoints first (browser dev tools, Network tab)",
            "Playwright for pages that genuinely need a browser",
            "Respect robots.txt and terms of service",
        ),
    ),
    # ── Geolocation ──────────────────────────────────────────────────────
    Trap(
        id="GEO-001",
        category=Category.GEOLOCATION,
        severity=Severity.WARNING,
        title="Live location tracking by polling GPS over HTTP",
        idea_patterns=(
            SERVICE_MARKETPLACE,
            r"\b(?:live|real[- ]?time)\b.*\b(?:location|gps|tracking|map)\b",
            r"\btrack\w*\b.*\b(?:location|drivers?|walkers?|couriers?|riders?|deliver\w*|vehicles?|fleet|runs?)\b",
            r"\bgps\b", r"\bride[- ]?(?:share|sharing|hailing)\b",
        ),
        anti_patterns=(r"\bpoll\w*\b", r"\bsetInterval\b", r"\bevery (?:\d+ )?seconds?\b", r"\bsend\w* (?:the )?(?:location|gps) every\b"),
        trap="Phones POSTing their GPS position every few seconds while other clients poll for it",
        why_it_fails=(
            "Fixed-interval GPS uploads drain the battery, flood your server with near-identical rows, and still "
            "show positions seconds late. iOS and Android also suspend apps in the background, so a plain timer "
            "simply stops firing the moment the walker or driver locks their phone."
        ),
        recommended=(
            "Platform background-location APIs (expo-location + TaskManager), throttled by distance (e.g. every 25 m), not time",
            "Stream positions to watchers over WebSockets or a managed realtime service (Supabase Realtime, Ably, Firebase)",
            "Mapbox or Google Maps SDK for display; store only the latest position plus a sampled history",
        ),
    ),
    Trap(
        id="GEO-002",
        category=Category.GEOLOCATION,
        severity=Severity.WARNING,
        title="Nearby search done in application code or with flat lat/lng math",
        idea_patterns=(
            SERVICE_MARKETPLACE,
            r"\bnear(?:by| me)\b", r"\bwithin \d+ ?(?:km|kilomet\w*|miles?|m)\b", r"\bclosest\b",
            r"\b(?:find|match)\w*\b.*\b(?:local|nearby|closest|near)\b",
        ),
        anti_patterns=(r"\bhaversine\b", r"\bpythagor\w*", r"\bloop\w* (?:over|through) (?:all|every)\b", r"\bsqrt\b"),
        trap="Loading every record and computing distances in app code, or treating lat/lng as flat x/y",
        why_it_fails=(
            "Scanning every walker or venue on each search slows down linearly as you grow. Treating latitude "
            "and longitude as a flat grid is also wrong: a degree of longitude shrinks towards the poles, so "
            "'nearest' results are simply incorrect outside the equator."
        ),
        recommended=(
            "PostGIS: ST_DWithin on a geography column with a GiST index (inside the Postgres you already use)",
            "SQLite apps: SpatiaLite, or a geohash prefix filter before exact distance",
            "For place search, Mapbox or Google Places instead of your own POI database",
        ),
    ),
    # ── Payments ─────────────────────────────────────────────────────────
    Trap(
        id="PAY-001",
        category=Category.PAYMENTS,
        severity=Severity.CRITICAL,
        title="Handling card data or marketplace payouts yourself",
        idea_patterns=(
            SERVICE_MARKETPLACE,
            r"\bpay(?:s|ing|ments?|outs?)?\b", r"\bcheckout\b", r"\bsubscriptions?\b", r"\bmarketplace\b",
            r"\bcharg\w*\b.*\b(?:customers?|users?|cards?|clients?)\b", r"\b(?:sell|buy)\w*\b.*\bonline\b",
        ),
        anti_patterns=(
            r"\bstor\w* (?:the |their )?(?:credit )?cards?\b", r"\bcard (?:numbers?|details)\b", r"\bcvv\b",
            r"\bpay (?:them|out|walkers|drivers|sellers|providers) (?:manually|by hand)\b", r"\bmanual payouts?\b",
        ),
        trap="Collecting card numbers in your own forms/database, or paying out sellers by hand",
        why_it_fails=(
            "Storing card data puts you under PCI DSS: audits, liability, and one leak can end the project. "
            "Marketplace payouts add identity checks (KYC), tax reporting and holding funds between buyer and "
            "seller. Building that by hand takes months and is legally risky."
        ),
        recommended=(
            "Stripe Checkout or Payment Element, so card data never touches your server",
            "Stripe Connect (Express accounts) for marketplace payouts, onboarding and KYC",
            "Store only Stripe IDs and integer-cent amounts; update order state from Stripe webhooks",
        ),
    ),
    # ── Notifications ────────────────────────────────────────────────────
    Trap(
        id="PUSH-001",
        category=Category.NOTIFICATIONS,
        severity=Severity.WARNING,
        title="Polling from the app to deliver notifications",
        idea_patterns=(
            r"\bnotif\w*", r"\bpush (?:alerts?|messages?)\b",
            r"\b(?:remind|alert)\w*\b.*\b(?:users?|phones?|customers?|owners?|walkers?|drivers?|people)\b",
        ),
        anti_patterns=(r"\bpoll\w*\b", r"\bsetInterval\b", r"\bcheck\w* (?:for (?:new )?\w+ )?every\b", r"\bbackground (?:loop|timer)\b"),
        trap="The app checking the server on a timer for new alerts",
        why_it_fails=(
            "Mobile operating systems suspend background apps, so a polling timer never fires when the app is "
            "closed, which is exactly when a notification matters. When it does run, it drains the battery."
        ),
        recommended=(
            "Expo Notifications (delivers via Apple APNs and Google FCM)",
            "Web Push with a service worker for browser apps",
            "Managed: OneSignal or Firebase Cloud Messaging",
        ),
    ),
)

_BY_ID: Dict[str, Trap] = {trap.id: trap for trap in TRAPS}


def get_trap(trap_id: str) -> Trap:
    """Look up a trap by id (e.g. ``"OCR-001"``). Raises ``KeyError`` if unknown."""
    return _BY_ID[trap_id.upper()]


def traps_in(category: Category) -> List[Trap]:
    """All traps in a category, in knowledge-base order."""
    return [trap for trap in TRAPS if trap.category is category]


def scan(idea: str) -> List[TrapWarning]:
    """Return a warning for every trap whose domain appears in ``idea``.

    A trap fires only when the idea is in its domain, so a stray word like
    "requests" can't trigger an unrelated trap. If the idea also names the
    anti-pattern, ``TrapWarning.severity`` escalates it to CRITICAL.
    """
    warnings: List[TrapWarning] = []
    for trap in TRAPS:
        domain_terms = trap.idea_matches(idea)
        if domain_terms:
            anti_terms = trap.anti_pattern_matches(idea)
            warnings.append(
                TrapWarning(trap=trap, matched_terms=tuple(domain_terms), anti_pattern_terms=tuple(anti_terms))
            )
    return warnings
