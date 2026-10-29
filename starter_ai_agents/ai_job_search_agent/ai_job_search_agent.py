import json

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run.base import RunStatus
from agno.tools.apify import ApifyTools

# The Apify Actor that fetches LinkedIn job listings, and the input that caps
# how many jobs one run may return.
JOB_ACTOR = "johnvc/linkedin-jobs-api"
ITEM_CAP = ("maxJobs", 10)

# Column name -> the Actor's dataset field.
KEEP_FIELDS = {
    "title": "title",
    "company": "companyName",
    "location": "location",
    "posted": "postedDate",
    "link": "jobUrl",
}

POSTED_WITHIN = ["Past 24 hours", "Past week", "Past month", "Any time"]


def make_cap_and_trim(rows: list):
    """Build a tool hook that caps the run size, trims each job and collects the rows."""

    def cap_and_trim(function_name: str, func: callable, args: dict):
        if not function_name.startswith("apify_actor_"):
            return func(**args)

        # Agno runs the tool with this same `args` dict, not with what the hook
        # passes to func, so the cap has to be written into it in place.
        # The parameters are usually flat, but may be nested under "kwargs".
        if isinstance(args.get("kwargs"), str):
            try:
                args["kwargs"] = json.loads(args["kwargs"])
            except ValueError:
                pass
        params = args["kwargs"] if isinstance(args.get("kwargs"), dict) else args

        # Clamp the item cap before the Actor run starts
        cap_name, cap_value = ITEM_CAP
        try:
            requested = int(params.get(cap_name) or cap_value)
        except (TypeError, ValueError):
            requested = cap_value
        params[cap_name] = max(1, min(requested, cap_value))

        result = func(**args)
        try:
            items = json.loads(result)
        except (TypeError, ValueError):
            return result

        # Keep only the fields the agent needs
        trimmed = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if "error" in item:
                trimmed.append(item)  # keep tool errors visible to the model
            elif item.get("result_type", "job") == "job":
                row = {key: item.get(field) for key, field in KEEP_FIELDS.items()}
                trimmed.append(row)
                # Keep at most cap_value rows in total, even across several calls
                if len(rows) < cap_value and row["link"] not in {r["link"] for r in rows}:
                    rows.append(row)
        return json.dumps(trimmed)

    return cap_and_trim


def search_jobs(keywords: str, location: str, posted_within: str, apify_api_token: str, openai_api_key: str):
    """Run the job search agent once. Returns the agent's answer and the job rows."""
    rows = []
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2", api_key=openai_api_key),
        tools=[ApifyTools(actors=[JOB_ACTOR], apify_api_token=apify_api_token)],
        tool_hooks=[make_cap_and_trim(rows)],
        instructions=[
            "Search for jobs with the Apify tool. Make one search call and fill only the keyword, location and posting window from the request.",
            "Answer with a short summary of what you found, then a table of title, company, location, posted date and link.",
        ],
        markdown=True,
    )
    request = f"Find {keywords} jobs in {location}"
    if posted_within != "Any time":
        request += f" posted in the {posted_within.lower()}"
    response = agent.run(request + ".")
    if response.status == RunStatus.error:
        raise RuntimeError(response.content)
    return response.content, rows


def main():
    st.title("AI Job Search Agent 💼")
    st.caption("Search LinkedIn job listings by keyword, location and posting date with an Agno agent and GPT-5.2")

    apify_api_token = st.sidebar.text_input("Enter Apify API Token", type="password")
    openai_api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

    keywords = st.text_input("Job title or keywords", placeholder="Python data engineer")
    location = st.text_input("Location", placeholder="Berlin")
    posted_within = st.selectbox("Posted within", POSTED_WITHIN, index=1)

    if st.button("Search Jobs"):
        if not apify_api_token or not openai_api_key:
            st.warning("Please enter your Apify API token and OpenAI API key in the sidebar.")
        elif not keywords or not location:
            st.warning("Please enter both keywords and a location.")
        else:
            with st.spinner("Searching LinkedIn jobs..."):
                try:
                    answer, rows = search_jobs(keywords, location, posted_within, apify_api_token, openai_api_key)
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                else:
                    if rows:
                        st.subheader(f"{len(rows)} jobs found")
                        st.dataframe(
                            rows,
                            column_config={"link": st.column_config.LinkColumn("link")},
                            hide_index=True,
                            use_container_width=True,
                        )
                    else:
                        st.info("No jobs found. Try broader keywords or a longer posting window.")
                    with st.expander("Agent summary"):
                        st.markdown(answer)
    else:
        st.info("Enter your API keys in the sidebar, fill in the search, then click 'Search Jobs'.")


if __name__ == "__main__":
    main()
