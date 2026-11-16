"""Warm, honest first emails to founders + follow-ups in the same tone.

Each entry: company, founder full name, website domain, hook (what genuinely interests you about
their work), idea (one concrete thing you could build), short idea (for subject/follow-ups).
"""

FOUNDERS = [
 ("Theo", "Miles Pines", "theo.site",
  "Theo's idea of an agent that doesn't just build a small business's website but keeps it getting found is exactly the kind of practical AI I like. Most owners never touch their site after launch.",
  "an automated SEO and content audit that Theo's agent could run on every site it manages", "automated SEO audits"),
 ("Hesper AI", "Pankaj Dhariwal", "gethesperai.com",
  "An AI that investigates a P&C claim end to end, instead of only summarising documents, is a real step up from most insurance AI.",
  "a prototype that pulls a claim timeline and red flags out of a sample claim file", "claim-timeline extraction"),
 ("Cohesive", "Kevin Zhang", "cohesiveapp.com",
  "An agentic CRM for blue-collar businesses makes a lot of sense. Those owners spend their days on job sites, not in a CRM.",
  "a lead-qualification flow with evals for one trade, like HVAC", "lead-qualification evals"),
 ("Obin AI", "Apoorv Saxena", "obin.ai",
  "Putting agentic workers inside regulated banks is a hard problem, and having run AI at JPMorgan makes your take on it especially interesting.",
  "an evaluation harness for one agent workflow on synthetic financial documents", "an agent eval harness"),
 ("ActionAI", "Miriam Haart", "actionai.co",
  "ActionAI's focus on making AI automations reliable enough for mission-critical work tackles the part most teams skip, and it resonated with me.",
  "a reliability test suite for one of your AI automations", "a reliability test suite"),
 ("Financial Datasets", "Virat Singh", "financialdatasets.ai",
  "Giving AI agents clean, reliable access to market data is infrastructure every finance-agent builder needs, and Financial Datasets' developer-first approach stood out to me.",
  "an open-source MCP server for the Financial Datasets API, with a short write-up developers could follow", "an MCP server for your API"),
 ("Traversal", "Anish Agarwal", "traversal.com",
  "Using causal ML to find the root cause of production incidents is a fascinating idea, and it tackles something every on-call engineer dreads.",
  "an incident-triage evaluation set built on a public dataset", "an incident-triage eval set"),
 ("Antares Labs", "Noaman Ahmad", "antareslabs.ai",
  "Congratulations on the launch. \"AI built inside the business, not bolted on top\" is exactly how I think about AI tools.",
  "a small proof of concept for one client workflow, like lease abstraction", "a lease-abstraction prototype"),
 ("definity", "Roy Daniel", "definity.ai",
  "Agentic data engineering for Spark and the lakehouse is a real need. Pipelines break in ways that take engineers hours to trace.",
  "a demo agent that explains a failed Spark job from its logs", "a Spark failure-explainer agent"),
 ("Stitch Studio", "Karan Mishra", "stitchstudio.ai",
  "Deploying governed AI agents in underwriting and claims is hard to do well, and the governance part is what most agent platforms skip.",
  "an explainable risk-scoring prototype for one underwriting step", "explainable underwriting scoring"),
 ("Tavern Research", "Matt Lackey", "tavernresearch.com",
  "Tavern's mix of polling, message testing and AI-assisted creative is a smart use of AI, because fast iteration on messaging is where LLMs shine.",
  "a small tool that clusters and summarises open-ended survey responses with an LLM", "LLM survey-response clustering"),
 ("AviaryAI", "Blesson Abraham", "helloaviary.ai",
  "Running outbound voice agents for banks and credit unions on a private LLM is a thoughtful approach for an industry where data can't leave the building.",
  "an evaluation set for one voice-agent conversation flow", "voice-agent evals"),
 ("Xenia", "Kumeil Hosain", "xenia.team",
  "Using AI on video, voice and photos to help frontline teams stay compliant goes well beyond the checklists most operations tools stop at.",
  "a prototype that turns photo or voice inspection notes into a structured checklist", "voice-to-checklist inspections"),
 ("VitVio", "Thomas Knox", "vitvio.com",
  "Bringing AI into the operating room to show hospitals how surgeries actually run is a high-impact problem that few people are working on.",
  "an analytics dashboard prototype on sample OR timing data", "an OR analytics prototype"),
 ("Layer Health", "David Sontag", "layerhealth.com",
  "Using LLMs for chart review and registry abstraction takes on one of the most manual jobs in healthcare, and Layer Health's research roots really show.",
  "an extraction-accuracy evaluation for one registry field", "a registry-extraction eval"),
 ("Loman AI", "Christian Wiens", "loman.ai",
  "An AI phone agent that answers restaurant calls during the dinner rush solves a very real problem. Missed calls are missed orders.",
  "an evaluation set of tricky restaurant calls for your phone agent", "a phone-agent eval set"),
 ("Hello Patient", "Alex Cohen", "hellopatient.com",
  "AI agents that handle patient calls and messages give front-desk teams hours back, and patients stop waiting on hold.",
  "an evaluation set of tricky patient-scheduling conversations", "patient-conversation evals"),
 ("RapidCanvas", "Rahul Pangam", "rapidcanvas.ai",
  "Congratulations on the Series B. Building enterprise AI apps together with in-house experts is a model that clearly works.",
  "a small, scoped piece of one of your client builds", "help on a client build"),
 ("Skribe.ai", "Tom Irby", "skribe.ai",
  "Bringing AI to depositions is a great fit for LLMs. Lawyers need accurate, searchable records, fast.",
  "a prototype that searches and summarises a deposition transcript", "deposition search and summaries"),
 ("ContextQA", "Deep Barot", "contextqa.com",
  "AI-driven test automation matters more every month, as teams ship more AI-written code that still has to be verified.",
  "a prototype that generates test cases from a user story", "user-story-to-test generation"),
 ("Actual AI", "Ethan Byrd", "actual.ai",
  "Guardrails for AI-native engineering teams is very timely. Teams now ship faster with AI than they can review the code.",
  "a demo check that catches one risky AI-generated code pattern", "a guardrail check for AI code"),
 ("Howie", "Austin Petersmith", "howie.ai",
  "An AI scheduling assistant that works entirely over email is a clean design, since nobody has to learn a new app.",
  "an evaluation set of tricky scheduling emails", "scheduling-email evals"),
 ("Yoodli", "Varun Puri", "yoodli.ai",
  "AI roleplay for sales coaching is a great product. Reps finally get to practise before the calls that matter.",
  "a scoring rubric and grader for one sales-roleplay scenario", "a roleplay grader"),
 ("Northslope", "Bill Ward", "northslope.com",
  "Congratulations on the Series A. Building mission-specific AI apps on Palantir is a focused niche, and it sounds like a fun place to build.",
  "a small, scoped piece of one of your client builds", "help on a client build"),
 ("Bernard", "Dan Katzman", "bernardhq.com",
  "AI employees for appliance-repair companies is a sharp niche: a trade full of phone calls, scheduling and parts lookups that AI can genuinely take off people's plates.",
  "a parts-lookup assistant that matches a customer's description to the right part", "a parts-lookup assistant"),
 ("Elimentary", "Yogesh Gorjilla", "elimentary.com",
  "Agents that run middle- and back-office work for private capital is a strong wedge. So much of that work still lives in spreadsheets and email.",
  "a document-extraction agent for capital-call notices", "capital-call extraction"),
 ("Floracene", "Asaph Kupferman", "floracene.com",
  "Letting healthcare teams vibe-code HIPAA-compliant internal tools without an engineering team is a clever unlock.",
  "a set of example internal-tool templates and evals for common clinic workflows", "clinic tool templates"),
 ("KelAI", "Jeremie Cohen", "kelaitech.com",
  "An autonomous AI quant that generates and tests ideas for funds is an ambitious and exciting build.",
  "a backtesting harness for LLM-generated trading ideas", "an idea-backtesting harness"),
 ("Leaping", "Adrien Philardeau", "leaping.io",
  "Automating bug resolution with AI is one of the most useful things AI can do for engineering teams.",
  "an evaluation set of real-world bugs to benchmark fix quality", "a bug-fix benchmark"),
 ("Pleom", "Royce Arockiasamy", "pleom.com",
  "Agentic business intelligence that turns company data into insights is very close to the dashboards and data tools I build.",
  "a natural-language-to-dashboard prototype on a sample dataset", "natural-language dashboards"),
 ("Auctor", "William Sun", "getauctor.com",
  "An agentic operating system for system integrators tackles a real pain: implementation projects that drift from what they were meant to deliver.",
  "an agent that turns a statement of work into a checklist of deliverables", "an SOW-to-deliverables agent"),
 ("Prosper AI", "Xavier de Gracia", "getprosper.ai",
  "Voice AI agents that handle healthcare calls for providers is high-impact work, and your growth this year shows how much it's needed.",
  "an evaluation set of tricky payer-call scenarios", "payer-call evals"),
 ("Assured", "Varun Krishnamurthy", "withassured.com",
  "Agents for provider credentialing remove a real bottleneck. Getting clinicians enrolled is notoriously slow.",
  "a prototype that extracts and checks credentialing fields from sample documents", "credentialing extraction"),
 ("Letter AI", "Ali Akhtar", "letter.ai",
  "Letter AI's role-play coaching is a great product, and it's great to see a Chicago AI company grow this fast.",
  "a scoring rubric and grader for one sales role-play scenario", "a role-play grader"),
 ("Fynite", "Tahir Warraich", "fynite.ai",
  "Turning business requirements into governed apps, workflows and agents is exactly the kind of work I enjoy most.",
  "a small agent for one common back-office workflow", "a back-office workflow agent"),
 ("Perspectives Health", "Eshan Dosani", "perspectiveshealth.ai",
  "Using AI agents to cut admin work and insurance denials for behavioural-health programs is meaningful work.",
  "a prototype that flags likely insurance-denial reasons in sample notes", "denial-risk flagging"),
 ("Draftbit", "Brian Luerssen", "draftbit.com",
  "Building real apps from natural-language prompts with AI coding agents is a fun space, and Draftbit has been at it longer than most.",
  "an evaluation set of app-building prompts to benchmark agent output", "an app-building eval set"),
 ("Teragonia", "Thomas Thayyil Thomas", "teragonia.com",
  "Giving PE sponsors one view of portfolio performance, with recommended actions, is a smart and data-heavy problem.",
  "a KPI anomaly-detection prototype on sample portfolio data", "portfolio KPI anomaly detection"),
 ("Ekpa", "Anant Asthana", "goekpa.com",
  "Autonomous research agents for trading is an exciting and demanding use of LLMs.",
  "a research-agent evaluation that checks claims against source filings", "a research-agent fact checker"),
 ("Synthpop", "Elad Ferber", "synthpop.ai",
  "Automating healthcare administrative work with AI gives clinicians time back for patients.",
  "a prototype that extracts referral details from faxed documents", "referral extraction"),
 ("Mia Labs", "Brian Hoang", "mialabs.ai",
  "An AI agent for car dealerships is a smart vertical. Dealers lose a lot of leads to slow responses.",
  "an evaluation set of tricky dealership customer conversations", "dealership-conversation evals"),
 ("Autonomize AI", "Ganesh Padmanabhan", "autonomize.ai",
  "Agentic AI for healthcare operations is meaningful work, with a huge amount of manual effort to remove.",
  "a prototype that summarises prior-authorisation documents", "prior-auth summaries"),
 ("CopilotKit", "Atai Barkai", "copilotkit.ai",
  "CopilotKit is exactly my kind of tooling. I build in-app AI assistants myself and like the agent-native UI direction.",
  "an open-source example app or integration guide for CopilotKit", "a CopilotKit example app"),
 ("Oumi", "Manos Koukoumidis", "oumi.ai",
  "An open platform for building foundation models is great for everyone who wants to understand and own their models.",
  "an evaluation recipe or tutorial notebook for the Oumi platform", "an Oumi eval recipe"),
 ("Owl AI", "Jay Prasad", "owlai.com",
  "AI judging for sports like snowboarding halfpipe is a really fun application, and fairer scoring matters to athletes.",
  "a scoring-consistency analysis comparing AI and human judges on sample runs", "judge-consistency analysis"),
 ("LightTable", "Paul Zeckser", "lighttable.ai",
  "AI review of construction drawings before building starts saves very expensive mistakes.",
  "a prototype that cross-checks dimensions between two drawing sheets", "drawing cross-checks"),
 ("Atolio", "David Lanstein", "atolio.com",
  "Permission-aware enterprise AI search is close to the RAG and vector-search work I do, and the permissions part is what most teams get wrong.",
  "a retrieval-quality evaluation for permission-filtered search", "permission-aware retrieval evals"),
 ("Liminal", "Steven Walchek", "liminal.ai",
  "Controlling what employees send to generative AI models is a very timely problem as GenAI spreads through companies.",
  "a prototype that detects sensitive data in prompts before they leave the company", "prompt sensitive-data detection"),
 # ---- added 10 Nov: more YC / seed AI startups (NYC, Seattle, SF) ----
 ("Arzana", "William Alexander", "arzana.com",
  "Adaptive AI built for manufacturers, starting with the sales-admin work that eats so much of a manufacturer's week, is a very practical place to start.",
  "a prototype that turns emailed RFQs into structured quote drafts", "RFQ-to-quote drafts"),
 ("Cohesion", "Devon Krapcho", "cohesionplatform.com",
  "An agentic teammate for public-equities teams is a great use of LLMs. Analysts drown in filings, transcripts and notes.",
  "a tool that compares an earnings call against the previous quarter's guidance", "earnings-call comparisons"),
 ("Ekho Labs", "Alina Park", "ekholabs.com",
  "A world model for freight that predicts logistics risk before it happens is an ambitious idea, and close to the real-time risk-scoring engine I built with weather and road-safety data.",
  "a prototype risk score that combines weather and route data for a set of shipments", "weather-aware shipment risk"),
 ("Kimpton", "Jack Zumwalt", "kimpton.ai",
  "Live evaluation arenas for financial work answer the question every firm adopting AI asks: is the model actually good at our work?",
  "a small set of financial-analysis tasks with graders for your arena", "graded finance tasks"),
 ("Vespin", "Charles Pan", "vespin.dev",
  "An inbox for coding agents is a clever answer to a real problem. Once you run several agents, keeping track of what each one did gets messy.",
  "an integration that brings one more coding agent's activity into Vespin", "a new agent integration"),
 ("Chamber", "Charles Ding", "usechamber.io",
  "An AIOps agent for ML teams is something I'd have loved to have. Training jobs fail in ways that can eat whole days.",
  "a demo that diagnoses a failed training job from its logs and metrics", "training-failure diagnosis"),
 ("Archal", "Aidan Tiruvan", "archal.ai",
  "API sandboxes built for AI agents fill a real testing gap. Nobody wants to let an agent loose on production APIs.",
  "a sandbox mock for one popular API, with tests", "a new API sandbox"),
 ("Arga Labs", "Phillip Li", "argalabs.com",
  "Real-world sandboxes to test and train AI agents are exactly what agent builders are missing.",
  "a test-scenario pack for one common agent workflow", "an agent test-scenario pack"),
 ("Corelayer", "Mitch Radhuber", "corelayer.com",
  "An AI production engineer for regulated industries takes on the hard version of incident response, where every action needs an audit trail.",
  "an incident-investigation evaluation on a public dataset", "incident-investigation evals"),
 ("HyperProbe", "Shailendra Singh", "hyperprobe.co",
  "An AI engineer that debugs and fixes production incidents in real time is a bold product, and exactly the kind of agent work I enjoy.",
  "a set of reproducible incident scenarios to benchmark fixes", "incident benchmark scenarios"),
 ("Glen", "Nikos Dritsakos", "tryglen.com",
  "An institutional learning layer, so every agent in a company learns from past work, is a smart idea. It's close to the feedback loop I built into PreQue AI, which learns from user corrections.",
  "a demo that shows an agent improving from stored past corrections", "an agent-memory demo"),
 ("Trope", "Matthew Chow", "trope.ai",
  "An AI forward-deployed engineer that puts custom agents into ERPs tackles the messiest part of enterprise AI: the integration.",
  "a small agent that reconciles purchase orders against invoices", "PO-invoice reconciliation"),
 ("Zomma", "Jihyun Kim", "zommalabs.com",
  "An AI BPO for financial services, run by computer-use agents, is an ambitious way to bring agents into back offices.",
  "an evaluation set of back-office tasks for computer-use agents", "computer-use task evals"),
 ("Rational", "Jibril Moinuddin", "rational.to",
  "A zero-human accounting firm is a bold idea, and accounting is full of the structured, repetitive work agents do well.",
  "a prototype that categorises bank transactions and flags anomalies", "transaction categorisation"),
 ("Vestris", "Joshua Tang", "vestris.ai",
  "An AI-native platform for real estate closings takes on a process that still runs mostly on PDFs and email chains.",
  "a prototype that extracts key dates and parties from closing documents", "closing-document extraction"),
 ("Veltha", "Edin Citaku", "veltha.ai",
  "An AI-native TPA starting with workers' comp is a sharp wedge into a paperwork-heavy industry.",
  "a prototype that turns a workers' comp claim file into a timeline", "claim-file timelines"),
 ("Zolvo", "Tony Montes", "zolvo.com",
  "AI for commercial lending is a great fit. So much of lending is reading financial statements and covenants.",
  "a prototype that checks loan covenants against a borrower's financial statements", "covenant checks"),
 ("RealPact", "Ranvir Deshmukh", "realpact.ai",
  "An AI-native operating system for real estate brokerages takes on a lot of paperwork that agents would rather not do.",
  "a contract-review assistant that flags missing clauses", "contract clause checks"),
 ("Savant", "Anthony Kim", "heysavant.com",
  "A company brain that AI-native enterprises run on is very close to the semantic-search work I've done.",
  "a retrieval-quality evaluation for company knowledge search", "retrieval evals"),
 ("Mireye", "Ansh Chokshi", "mireye.com",
  "A search engine for the physical world is a fascinating idea, and close to the geospatial risk engine I built across Mumbai and Bengaluru.",
  "a demo agent that answers location questions by combining your API with weather and road data", "a geospatial agent demo"),
 ("Speko", "Beknazar Abdikamalov", "speko.ai",
  "Routing every voice-AI call to the best speech model is a smart way to handle a model landscape that changes every month.",
  "a benchmark of speech models on Indian-accented English", "an accent benchmark"),
 ("Caretta", "Kayra Bahadir", "caretta.so",
  "Real-time AI for sales calls is a hard engineering problem: useful suggestions in seconds, not after the call.",
  "an evaluation set of sales-call moments with ideal suggestions", "sales-call evals"),
 ("Antinuous", "Ricardo Nunez", "antinuous.com",
  "Autonomous research agents for R&D and applied science is the kind of agent work I find most exciting.",
  "a literature agent that extracts results tables from papers", "a results-extraction agent"),
 ("Assemble", "Aliyan Ishfaq", "assemble.ai",
  "Autonomous IT delivery is a big opportunity, since so many IT requests are repetitive and well defined.",
  "an agent that handles one common IT request end to end, like access provisioning", "an IT-request agent"),
 ("Minicor", "Faizaan Chishtie", "minicor.com",
  "Scalable Windows desktop automation is underrated. Most legacy business software has no API.",
  "an automation for one legacy desktop workflow, with proper error handling", "a desktop workflow automation"),
 ("Sherpa", "Ethan Kinnan", "withsherpa.ai",
  "Websites that improve themselves is a fun idea, and conversion optimisation suits agents that can run experiments.",
  "an agent that proposes and scores landing-page variants", "landing-page variant scoring"),
 ("Luca IQ", "Angelo Policicchio", "lucaiq.com",
  "An API-first tax engine for CPA firms and developers is a smart way to bring structure to tax work.",
  "an example app or agent built on your API", "an example app on your API"),
 ("Tsenta", "Agnay Srivastava", "tsenta.com",
  "An AI career agent that finds matching jobs and applies for you is something I relate to directly, as a student looking for work right now.",
  "an evaluation of job-to-profile match quality on sample listings", "match-quality evals"),
 # founders for companies first emailed through a shared inbox
 ("Cloverleaf AI", "Adam Zucker", "cloverleaf.ai",
  "Turning public-sector meetings and budgets into sales leads is a great use of LLMs. There's a huge amount of unstructured text that nobody has time to read.",
  "a prototype that pulls sales signals out of a city-council meeting transcript", "meeting-transcript signals"),
 ("BuildQ", "Maryssa Barron", "buildq.ai",
  "Using AI to speed up clean-energy project development and finance is meaningful work. A $200M solar project shouldn't sit for weeks while someone reads documents.",
  "a prototype that pulls key terms and risks out of a solar project document", "solar-document extraction"),
]

# Cities for the startups above (used to pick the right morning time zone)
EXTRA_CITY = {"Arzana": "New York", "Cohesion": "New York", "Ekho Labs": "New York", "Kimpton": "New York",
              "Vespin": "New York", "Chamber": "Seattle", "Cloverleaf AI": "Denver", "BuildQ": "Las Vegas"}
SF_DEFAULT = "San Francisco"

SIG = "Best,\nAnushree Revankar\ngithub.com/Anushre2005 · linkedin.com/in/anushree-revankar"

FIRST = """Hi {first},

{hook}

I'm Anushree, a computer engineering student in Mumbai (honours in Data Science & AI) who builds AI tools for real users. I've done freelance projects, and during my internship at HTL I built PreQue AI, a Claude-powered app that automates pre-qualification forms, with semantic search over a vector store and a feedback loop that learns from corrections.

While reading about {company}, one idea came to mind: {idea}. It's the kind of thing I could prototype in a few days.

I'd love to hear what you're working on and whether a small, fixed-scope project could be useful to you. Would you be open to a 15-minute call in the next couple of weeks?

{sig}"""

PRIOR_PS = "\n\nP.S. I also wrote to your team inbox on {date} and wanted to reach you directly as well."

FU1 = """Hi {first},

Just checking you saw my last email. I'd really like to help {company} with AI work, even on something small to start.

Would you have 15 minutes for a quick call this week or next?

Thanks,
Anushree"""

FU2 = """Hi {first},

I know you're busy, so I'll keep this short. I'm happy to start with one small task, so you can see how I work before deciding anything. Some of my projects are here: github.com/Anushre2005

Thanks,
Anushree"""

FU3 = """Hi {first},

This is my last note, as I don't want to fill your inbox. If you ever need help building AI tools, I'd love to hear from you. And if someone else at {company} is the better person to talk to, I'd be grateful if you could point me to them.

All the best,
Anushree"""

# Follow-ups for emails that went to a team inbox: same plain text
GENERIC_FU1 = FU1

PROF_FU1 = """{greeting}

I'm following up on my email about a remote research internship in your lab. I'm happy to start with any small task, like cleaning a dataset or reproducing a result from one of your papers.

Thank you for your time,
Anushree Revankar"""

PROF_FU2 = """Dear {first},

One last short note. If a remote internship isn't possible right now, could you point me to a student or postdoc in your lab I could reach out to? I'd really appreciate it.

Thank you,
Anushree Revankar"""


def first_email(company, person, hook, idea, prior_date=None):
    body = FIRST.format(first=person.split()[0], hook=hook, company=company, idea=idea, sig=SIG)
    if prior_date:
        from datetime import date as _d
        d = _d.fromisoformat(prior_date)
        body += PRIOR_PS.format(date=f"{d.day} {d.strftime('%B')}")
    return body


def subject_for(company, short):
    return f"Idea for {company}: {short}"
