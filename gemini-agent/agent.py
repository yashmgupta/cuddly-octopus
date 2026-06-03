import asyncio
import json
import os
import inspect
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ✅ Free tier: uses Google AI Studio API key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class AutonomousAgent:
    def __init__(self, storage_file="skills_database.json"):
        self.storage_file = storage_file
        # Base hardcoded capabilities
        self.known_skills = {
            "fetch_weather": {
                "description": "Defines and returns local atmospheric weather conditions.",
                "code": "def fetch_weather():\n    print('The weather is currently sunny and 72\u00b0F.')"
            }
        }
        self.load_skills_from_disk()

    def load_skills_from_disk(self):
        """Loads permanently saved skills from a local JSON file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    saved_skills = json.load(f)
                    self.known_skills.update(saved_skills)
                print(f"\ud83d\udcbe Loaded {len(saved_skills)} saved skill(s) from {self.storage_file}")
            except Exception as e:
                print(f"\u26a0\ufe0f Could not load saved skills: {e}")

    def save_skill_to_disk(self):
        """Saves current learned skills to long-term JSON storage."""
        skills_to_save = {k: v for k, v in self.known_skills.items() if k != "fetch_weather"}
        try:
            with open(self.storage_file, "w") as f:
                json.dump(skills_to_save, f, indent=4)
        except Exception as e:
            print(f"\u26a0\ufe0f Failed to save skills to disk: {e}")

    async def execute_task(self, prompt: str):
        print(f"\n\ud83e\udd16 User Prompt: '{prompt}'")

        # Build the dynamic manifest to show Gemini what tools are already available
        skills_manifest = {name: data["description"] for name, data in self.known_skills.items()}

        system_instruction = f"""
        You are a Semantic Router for an AI Agent. Match the user's intent against these local skills:
        {json.dumps(skills_manifest, indent=2)}

        CRITICAL ROUTING RULES:
        1. If the intent matches an existing skill (even with typos or alternative phrasing), reply exactly with:
           MATCH: <skill_name> | ARG: <extracted_search_query_or_value>

        2. If NO skill matches, generate a brand-new Python function to handle it.
           - Start your response exactly with: NEW_SKILL: <function_name> | DESC: <brief_description>
           - Provide ONLY valid Python code inside standard markdown syntax blocks.
           - CRITICAL: For web searching, always use the 'googlesearch' module exactly like this:
             from googlesearch import search
             for url in search(query_string, num_results=3):
                 print(url)
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )

        decision_text = response.text.strip()
        first_line = decision_text.split('\n')[0]

        if "MATCH:" in first_line:
            parts = first_line.split("|")
            skill_name = parts[0].replace("MATCH:", "").strip()
            arg_val = parts[1].replace("ARG:", "").strip()

            print(f"\u2705 Semantic Match Found: Routing to local tool '{skill_name}'")
            parsed_arg = arg_val.strip("'\"") if arg_val != "None" else None
            await self.run_local_tool(skill_name, parsed_arg)

        elif "NEW_SKILL:" in first_line:
            parts = first_line.split("|")
            skill_name = parts[0].replace("NEW_SKILL:", "").strip()
            description = parts[1].replace("DESC:", "").strip()

            print(f"\u26a1 No matching skill found. Generating new tool: '{skill_name}'")
            cleaned_code = decision_text.split("```python")[-1].split("```")[0].strip()

            # Save new skill to storage
            self.known_skills[skill_name] = {"description": description, "code": cleaned_code}
            self.save_skill_to_disk()
            print(f"\ud83d\udcbe Saved '{skill_name}' to database.")

            # Extract clean parameters from prompt
            extracted_arg = re.findall(r"['\"]([^'\"]*?)['\"]", prompt)
            arg_to_pass = extracted_arg[0] if extracted_arg else prompt
            await self.run_local_tool(skill_name, arg_to_pass)

    async def run_local_tool(self, skill_name: str, parsed_argument=None):
        code_str = self.known_skills[skill_name]["code"]

        from googlesearch import search

        local_context = {"search": search}
        global_context = globals().copy()
        global_context["search"] = search

        try:
            exec(code_str, global_context, local_context)
            func = local_context.get(skill_name) or global_context.get(skill_name)

            if func:
                sig = inspect.signature(func)
                if len(sig.parameters) > 0 and parsed_argument is not None:
                    func(parsed_argument)
                else:
                    func()
            else:
                print("\u26a0\ufe0f Functional target execution scope missing.")
        except Exception as e:
            print(f"\ud83d\udea8 Runtime Error: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = AutonomousAgent()
    # Change the prompt below to test different tasks
    asyncio.run(agent.execute_task("What's the weather like?"))
