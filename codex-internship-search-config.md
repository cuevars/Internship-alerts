# Internship Finder: Broadened Search Config

## Current implementation and scanning behavior

The sections below preserve the supplied **proposed expansion plan** and company seed list. They describe desired coverage, not sources already connected. The executable source of truth today is `config.json`; this Markdown file does not change the running script by itself.

### Does it constantly scan?

The GitHub Actions workflow requests a scan **every 30 minutes**, at minutes **07 and 37 of each hour**. It is scheduled polling, not a continuous live connection. Each run downloads the configured listings, applies your location/eligibility filters and weighted score, and sends up to 15 unseen qualifying listings to ntfy. Saved listing IDs and application URLs prevent repeat alerts. Remaining new matches wait for later runs. A local `python radar.py` command runs once and exits.

Cloud scans require the updated files to be pushed to the default branch, Actions to be enabled, notification secrets to be configured, and the workflow to be able to save alert history. This document does not confirm the deployed workflow is currently running. GitHub can delay scheduled runs, and a company or community feed can lag a posting, so alerts are not guaranteed within exactly 30 minutes of publication.

### Why only those companies?

Hershey was the requested starting employer. Duolingo and Viking were initial additions with verified public employer feeds and relevant regional listings. They are a small first set, not a restriction on companies you can apply to. Simplify remains a separate community source covering many employers, but that is different from checking each employer directly.

| Source currently configured | How it is checked |
|---|---|
| SimplifyJobs Summer2027 | Public community listings JSON |
| The Hershey Company | Official internship career pages, including pagination |
| Duolingo | Employer-specific Greenhouse API |
| Viking Global Investors | Employer-specific Greenhouse API |

### Expansion status and priorities

All company names, government programs, role variants, and location lists in Sections 1–6 below are retained as **targets for expansion**. Their presence here does not activate monitoring. Prioritize cybersecurity vendors, banks/fintech, insurers, and NJ/PA corporate employers with cyber, IT, and data opportunities; include sophomore-friendly programs after checking their current eligibility and availability.

For each employer, verify its official careers URL and actual recruiting-system tenant/board before enabling it. Do not assume a guessed lowercase company token identifies the correct employer. Store verified endpoints in `config.json`; record unverified or unsupported sites as pending rather than counting them as scanned. Greenhouse and the Hershey-specific adapter are implemented today. Lever, Ashby, SmartRecruiters, Workday, government/program-page adapters, and logged-in job boards are proposed work, not implemented integrations.

The proposed broader terms, title variants, description scoring, minimum score of 5, and company/title/location deduplication below also remain proposals. Current behavior retains the previously configured minimum score of **3**, title/location scoring, Summer 2027 focus with explicitly labeled unspecified employer dates, three résumé recommendations, and ID/URL deduplication. Implement and test those broader changes before describing them as active.

## Proposed broadened search plan

Goal: find undergraduate internships (Summer 2027 and rolling) in cyber, IT, data, and fintech in NYC, NJ, and PA. Candidate is a CS undergrad (Network Security concentration), so freshman/sophomore-friendly programs matter.

## 1. Strategy: widen in four directions

1. **More title variants.** Many roles are not called "intern" (see `title_include`).
2. **More sources.** Query company ATS APIs directly, not just job boards (see Section 3).
3. **More locations.** Include every NYC/NJ/PA hub town, not just the big cities.
4. **Looser matching, then filter.** Pull broadly, then score and exclude, instead of strict keyword AND logic.

## 2. Config

```json
{
  "target_term": ["Summer 2027", "2027", "Fall 2026", "Spring 2027", "Rolling"],
  "title_include": [
    "intern", "internship", "co-op", "coop", "apprentice", "apprenticeship",
    "fellow", "fellowship", "early career", "early talent", "student",
    "undergraduate", "university", "campus", "summer analyst", "summer associate",
    "insight program", "externship", "trainee", "rotational", "junior"
  ],
  "title_exclude": [
    "senior", "sr.", "staff", "principal", "lead", "manager", "director",
    "vp", "vice president", "head of", "mba", "phd", "ph.d", "postdoc",
    "master's only", "graduate student", "attorney", "nurse", "physician"
  ],
  "role_keywords": {
    "cyber": [
      "cybersecurity", "cyber security", "information security", "infosec",
      "security analyst", "security engineer", "SOC", "security operations",
      "threat intelligence", "threat hunting", "incident response", "DFIR",
      "vulnerability management", "penetration testing", "pentest", "red team",
      "blue team", "GRC", "governance risk compliance", "IAM",
      "identity and access management", "application security", "appsec",
      "cloud security", "network security", "security architecture",
      "risk and compliance", "third party risk", "privacy", "cyber risk"
    ],
    "it": [
      "IT", "information technology", "help desk", "service desk",
      "desktop support", "technical support", "systems administrator",
      "sysadmin", "network engineer", "network administrator", "infrastructure",
      "cloud", "AWS", "Azure", "devops", "SRE", "site reliability",
      "IT project management", "IT operations", "IT audit", "technology risk",
      "technology analyst", "business systems analyst", "ServiceNow"
    ],
    "data": [
      "data analyst", "data analytics", "business analyst", "business intelligence",
      "BI analyst", "reporting analyst", "data science", "data engineer",
      "data engineering", "analytics", "SQL", "Tableau", "Power BI",
      "operations analyst", "quantitative analyst", "research analyst",
      "product analyst", "insights", "data operations", "data quality",
      "data governance", "data management"
    ],
    "data_entry_ops": [
      "data entry", "operations analyst", "operations intern", "administrative",
      "records", "claims", "document processing", "back office",
      "client services", "quality assurance", "QA", "business operations",
      "support analyst", "onboarding", "compliance operations"
    ],
    "fintech": [
      "fintech", "payments", "banking technology", "trading technology",
      "risk analyst", "fraud", "fraud analyst", "AML", "KYC", "financial crimes",
      "credit risk", "market risk", "operational risk", "treasury",
      "wealth technology", "insurtech", "regtech", "quant", "software engineer intern"
    ]
  },
  "locations": {
    "NY": [
      "New York, NY", "New York City", "NYC", "Manhattan", "Brooklyn", "Queens",
      "Bronx", "Staten Island", "Long Island", "Melville", "Uniondale", "Garden City",
      "White Plains", "Purchase", "Armonk", "Rye Brook", "Tarrytown", "Albany",
      "Hybrid - New York", "Remote - New York"
    ],
    "NJ": [
      "Jersey City", "Newark", "Hoboken", "Princeton", "Plainsboro", "Parsippany",
      "Morristown", "Basking Ridge", "Bedminster", "Bridgewater", "Somerset",
      "Piscataway", "Edison", "New Brunswick", "Iselin", "Roseland", "Teaneck",
      "Fort Lee", "Paramus", "Secaucus", "Short Hills", "Florham Park",
      "East Hanover", "Whippany", "Murray Hill", "Berkeley Heights",
      "Rahway", "Kenilworth", "Mahwah", "Weehawken", "Holmdel", "Red Bank",
      "Cherry Hill", "Mount Laurel", "Camden", "Trenton", "Lawrenceville"
    ],
    "PA": [
      "Philadelphia", "King of Prussia", "Malvern", "Wayne", "Conshohocken",
      "Radnor", "Berwyn", "Blue Bell", "Horsham", "Fort Washington", "Newtown",
      "West Chester", "Exton", "Oaks", "Wilmington DE (nearby)", "Allentown",
      "Bethlehem", "Reading", "Lancaster", "Harrisburg", "Hershey", "Middletown",
      "Lititz", "Pittsburgh", "Cranberry Township", "Canonsburg"
    ],
    "include_remote_us": true,
    "include_hybrid": true
  },
  "score": {
    "title_has_intern_term": 3,
    "title_has_role_keyword": 3,
    "description_has_role_keyword": 1,
    "location_match": 2,
    "mentions_2027": 2,
    "mentions_freshman_sophomore_or_rising_junior": 2,
    "min_score_to_keep": 5
  },
  "dedupe_on": ["company", "normalized_title", "location"],
  "output_fields": [
    "company", "title", "location", "url", "date_posted", "deadline",
    "role_category", "score", "source"
  ]
}
```

## 3. Sources to query

### A. Company ATS APIs (best coverage, structured JSON)
Loop over the company list in Section 4. For each company, try to find its board and hit the matching endpoint. Treat a 404 as "not on this ATS" and move on.

| ATS | Endpoint pattern |
|---|---|
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` |
| Lever | `GET https://api.lever.co/v0/postings/{company}?mode=json` |
| Ashby | `GET https://api.ashbyhq.com/posting-api/job-board/{name}` |
| SmartRecruiters | `GET https://api.smartrecruiters.com/v1/companies/{id}/postings` |
| Workday | `POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` with body `{"appliedFacets":{},"limit":20,"offset":0,"searchText":"intern"}` |

Notes:
- Board tokens are usually the lowercase company name with no spaces. Generate guesses, validate with a quick request, and cache the ones that work.
- Large banks, pharma, and insurers mostly use Workday, Taleo, iCIMS, or custom sites. For those, search with `searchText` set to each term in `title_include` and paginate.
- Add a short delay between requests and set a descriptive User-Agent.

### B. Community internship lists (easy wins)
- GitHub repos that track internships, such as the SimplifyJobs and Summer2027 internship lists. Parse their JSON/README tables and filter by the config above. Confirm the current repo names, since they change each season.

### C. Job boards
- Handshake (via NYIT login), LinkedIn, Indeed, Wellfound, Built In NYC, Dice, USAJobs (Pathways program, federal internships), Idealist (nonprofits).
- Respect each site's terms and robots.txt. Prefer official APIs, RSS feeds, and email alerts over scraping where scraping is not permitted.

### D. Government and program pages (often missed)
- USAJobs Pathways internships, NYC Cyber Command, NYC OTI, NJ OIT, NJCCIC, PA state IT, SFS CyberCorps, Federal Reserve Bank of NY, Philadelphia Fed.

## 4. Company seed list

```json
{
  "cyber_vendors": ["Palo Alto Networks","CrowdStrike","Okta","Datadog","Axonius","Snyk","Sonatype","Cisco","Fortinet","Rapid7","Arctic Wolf","Optiv","Trustwave","Mandiant","Zscaler","SentinelOne","Tenable","Proofpoint","Cloudflare","Wiz","Cyera","Armis","Varonis","KnowBe4"],
  "consulting_big4": ["Deloitte","PwC","EY","KPMG","Accenture","Booz Allen Hamilton","Protiviti","Guidehouse","CGI","Slalom","West Monroe","Capgemini","Cognizant"],
  "defense_gov_contractors": ["Lockheed Martin","Northrop Grumman","Leidos","Raytheon","General Dynamics","Thales","L3Harris","SAIC","CACI","ASRC Federal","Peraton","ManTech","Parsons","BAE Systems"],
  "government": ["NYC Cyber Command","NYC OTI","NJ OIT","NJCCIC","FBI","Federal Reserve Bank of New York","Federal Reserve Bank of Philadelphia","SEC","Picatinny Arsenal","MTA","Port Authority of NY & NJ","NYPD","CISA","USAJobs Pathways"],
  "banks_finance": ["JPMorgan Chase","Goldman Sachs","Morgan Stanley","Citi","Bank of America","Wells Fargo","Barclays","Deutsche Bank","Capital One","American Express","BNY Mellon","State Street","BlackRock","TIAA","PNC","Santander","HSBC","UBS","Nomura","Mizuho","MUFG","Natixis","Fidelity","Vanguard","Franklin Templeton","Invesco","Neuberger Berman","AllianceBernstein","Apollo","Blackstone","KKR","Carlyle","Two Sigma","Jane Street","Citadel","DE Shaw","Point72","Bloomberg","S&P Global","Moody's","MSCI","FactSet","Nasdaq","ICE","NYSE","DTCC","Broadridge","SS&C","SEI","Envestnet","TD Bank","Citizens","M&T Bank","Ally","Synchrony","Discover","Mastercard","Visa"],
  "fintech": ["Stripe","Plaid","Block","PayPal","Robinhood","Betterment","Wealthfront","Chime","Brex","Ramp","Mercury","Affirm","Carta","Addepar","Fiserv","FIS","Jack Henry","Toast","Marqeta","Paxos","Bilt","Blend","Flywire","Clearwater Analytics","Policygenius","Lemonade","Oscar Health","SoFi","Coinbase","Gemini","Kraken","Upstart","Adyen","Checkout.com"],
  "insurance": ["MetLife","Prudential","AIG","Chubb","New York Life","Northwestern Mutual","Travelers","The Hartford","Lincoln Financial","Penn Mutual","Cigna","Independence Blue Cross","Horizon BCBS","Empire BlueCross","Healthfirst","Fidelis Care","Verisk","Guardian","Mass Mutual","Allstate","Liberty Mutual","Nationwide","Aflac"],
  "tech_media": ["Google","Meta","Amazon","Microsoft","IBM","Apple","Oracle","Salesforce","Adobe","Spotify","Etsy","MongoDB","Squarespace","Twilio","Peloton","Zocdoc","Yext","Vimeo","Warby Parker","NBCUniversal","Disney","Warner Bros. Discovery","Condé Nast","New York Times","SeatGeek","Duolingo","Datadog","Shopify","Uber","Lyft","DoorDash","Pinterest","Reddit","Snap","Dropbox","Atlassian","ServiceNow","Workday","Intuit","Dell","HP","Intel","Nvidia"],
  "telecom_utilities": ["Verizon","AT&T","Comcast","Nokia Bell Labs","Con Edison","PSEG","National Grid","PECO","PPL","Exelon","T-Mobile","Lumen","Altice","Charter Spectrum"],
  "healthcare": ["Mount Sinai","NYU Langone","NewYork-Presbyterian","Northwell Health","Montefiore","NYC Health + Hospitals","Hackensack Meridian","RWJBarnabas","Atlantic Health","Penn Medicine","UPMC","Jefferson Health","Memorial Sloan Kettering","Columbia University Irving Medical Center","CVS Health","Aetna","UnitedHealth Group","Optum","Elevance Health"],
  "pharma_life_sciences": ["Pfizer","Merck","Johnson & Johnson","Bristol Myers Squibb","Novartis","Bayer","GSK","Teva","Regeneron","Zoetis","Becton Dickinson","AstraZeneca","Sanofi","Eli Lilly","Takeda","Thermo Fisher"],
  "corporate_hqs_nj_pa": ["ADP","Cognizant","Wakefern","Siemens","Panasonic","Sony","Samsung","Aramark","Hershey","Wawa","Sheetz","Highmark","Ansys","Comcast","Lockheed Martin","Crown Holdings","Campbell's","Church & Dwight","Colgate-Palmolive","Johnson Controls","TE Connectivity","Eastman","Air Products","PPG","Kraft Heinz","Dick's Sporting Goods","Rite Aid","Unisys","Vertex","Mastech","Ricoh"],
  "staffing_it_services": ["Robert Half","Kforce","TEKsystems","Insight Global","Randstad","Adecco","Kelly Services","Apex Systems","Infosys","Wipro","TCS","HCLTech","Capgemini","NTT Data","Tech Mahindra","LTIMindtree","DXC","Kyndryl","Concentrix"],
  "early_career_programs": ["Google STEP","Microsoft Explore","Meta University","JPMorgan Early Insights","JPMorgan Career Edge","Goldman Sachs Possibility Summit","Goldman Sachs Sophomore Internship","Citi sophomore program","Morgan Stanley sophomore program","Deloitte early career","PwC early career","KPMG early insight","EY early insight","Year Up","Pursuit","SEO Tech Developer","Tech Talent Pipeline NYC","HACU","Hispanic Scholarship Fund","SHPE","Latinas in Tech","Prospanica","Per Scholas","Break Through Tech","ColorStack"]
}
```

## 5. Matching logic (pseudocode)

```
for job in all_jobs:
    title = lower(job.title)
    text  = lower(job.title + " " + job.description)

    if any(x in title for x in title_exclude): skip
    if not in_target_location(job.location, locations): skip   # allow remote-US if enabled

    s = 0
    if any(x in title for x in title_include): s += 3
    if any(k in title for cat in role_keywords.values() for k in cat): s += 3
    if any(k in text  for cat in role_keywords.values() for k in cat): s += 1
    if "2027" in text or "summer 2027" in text: s += 2
    if any(x in text for x in ["freshman","sophomore","rising junior","first-year","undergraduate"]): s += 2
    s += 2  # location already matched

    if s >= min_score_to_keep: keep(job, s)

dedupe(kept, on=["company","normalized_title","location"])
sort by score desc, then date_posted desc
```

## 6. Practical tips for the script

- **Expand synonyms automatically.** Match "Security" and "Cyber" together, "Analyst" and "Associate", "Intern" and "Internship".
- **Don't require "intern" in the title for every source.** Some listings say "Summer Analyst," "Technology Associate (Undergraduate)," or "University Program."
- **Track what you've already seen.** Store job URLs in a local SQLite file or CSV so each run only reports new postings.
- **Run it on a schedule** (daily or weekly) and send new matches to email or a spreadsheet.
- **Log misses.** Save any company whose board could not be found so you can add its careers URL manually.
- **Use exact-date logic** for deadlines: many roles close when filled, so sort by newest first.
