## 💼 AI Job Search Agent

A Streamlit app that searches LinkedIn job listings with an Agno agent. You type a job title, a location and a posting window, and the agent fills the search, runs it, and returns a table of matching jobs. The job data comes from an Apify Actor called through Agno's `ApifyTools`; OpenAI's GPT-5.2 handles the request and the summary.

### Features

- **Plain search form**: keywords, location and a posted-within window (past 24 hours, week, month or any time)
- **Agno agent with ApifyTools**: the agent reads the Actor's input schema and fills the search parameters from your request
- **Capped and trimmed runs**: a tool hook limits each run to 10 jobs and keeps only title, company, location, posted date and link, so the context stays small and the run stays cheap
- **Results table**: matching jobs shown in a table with clickable links, plus the agent's short summary
- **Streamlit UI**: API keys are entered in the sidebar

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_job_search_agent
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

`apify-client` is pinned below 3 because Agno's `ApifyTools` reads the dict responses of apify-client 2.x.

3. Get your API keys

- Sign up for an [OpenAI account](https://platform.openai.com/) and create an API key.
- Sign up for an [Apify account](https://console.apify.com/) and copy your API token from Settings > API & Integrations.

4. Run the Streamlit app

```bash
streamlit run ai_job_search_agent.py
```

5. Enter your Apify API token and OpenAI API key in the sidebar, fill in the search, and click **Search Jobs**.

### How it works

- `ApifyTools(actors=["johnvc/linkedin-jobs-api"])` registers the Actor as a tool for the agent.
- The `cap_and_trim` tool hook clamps `maxJobs` to 10 before the run starts and trims each returned job to five fields.
- To use another job Actor, change `JOB_ACTOR`, `ITEM_CAP` and `KEEP_FIELDS` at the top of `ai_job_search_agent.py`.
