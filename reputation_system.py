# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class ReputationSystem(gl.Contract):

    owner: Address
    user_count: u256
    user_data: DynArray[str]

    def __init__(self, owner_address: Address):
        self.owner = owner_address
        self.user_count = u256(0)

    @gl.public.view
    def get_profile(self, user_address: str) -> str:
        score = self._get(user_address, "score")
        if not score:
            return "Profile not found"
        return (
            f"Address: {user_address} | "
            f"Score: {score} | "
            f"Level: {self._get(user_address, 'level')} | "
            f"Reviews: {self._get(user_address, 'review_count')} | "
            f"Summary: {self._get(user_address, 'summary')}"
        )

    @gl.public.view
    def get_user_count(self) -> u256:
        return self.user_count

    @gl.public.view
    def get_summary(self) -> str:
        return (
            f"GenLayer Onchain Reputation System\n"
            f"Total Profiles: {int(self.user_count)}"
        )

    @gl.public.write
    def register(self, github_url: str, description: str) -> str:
        caller = str(gl.message.sender_address)
        existing = self._get(caller, "score")
        assert not existing, "Profile already registered"
        assert len(github_url) >= 10, "GitHub URL is too short"

        self._set(caller, "github_url", github_url)
        self._set(caller, "description", description[:300])
        self._set(caller, "score", "0")
        self._set(caller, "level", "newcomer")
        self._set(caller, "review_count", "0")
        self._set(caller, "summary", "No reviews yet")

        self.user_count = u256(int(self.user_count) + 1)
        return f"Profile registered for {caller[:10]}..."

    @gl.public.write
    def evaluate_profile(self, user_address: str) -> str:
        github_url = self._get(user_address, "github_url")
        assert github_url, "Profile not found"

        description = self._get(user_address, "description")
        current_score = int(self._get(user_address, "score") or "0")
        review_count = int(self._get(user_address, "review_count") or "0")

        def leader_fn():
            web_data = ""
            try:
                response = gl.nondet.web.get(github_url)
                raw = response.body.decode("utf-8")
                web_data = raw[:3000]
            except Exception:
                web_data = "Could not fetch profile data."

            prompt = f"""You are an AI evaluator assessing a developer's reputation score
based on their public GitHub profile and self-description.

User Description: {description}

GitHub Profile Content:
{web_data}

Evaluate the developer's reputation considering activity, contributions, and profile quality.
Assign a score from 0 to 100 and a level based on this scale:

0 to 20: newcomer
21 to 40: beginner
41 to 60: intermediate
61 to 80: experienced
81 to 100: expert

Respond ONLY with this JSON:
{{"score": 75, "level": "experienced", "summary": "two sentences describing the developer profile"}}

score is an integer 0 to 100, level is one of the five options above,
summary is two sentences max describing what you found.
No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            score = int(data.get("score", 0))
            level = data.get("level", "newcomer")
            summary = data.get("summary", "")

            score = max(0, min(100, score))
            if level not in ("newcomer", "beginner", "intermediate", "experienced", "expert"):
                level = "newcomer"

            return json.dumps({
                "score": score,
                "level": level,
                "summary": summary
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)
                if leader_data["level"] != validator_data["level"]:
                    return False
                return abs(leader_data["score"] - validator_data["score"]) <= 10
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        new_score = data["score"]
        level = data["level"]
        summary = data["summary"]

        if review_count > 0:
            averaged_score = (current_score + new_score) // 2
        else:
            averaged_score = new_score

        new_review_count = review_count + 1

        self._set(user_address, "score", str(averaged_score))
        self._set(user_address, "level", level)
        self._set(user_address, "summary", summary)
        self._set(user_address, "review_count", str(new_review_count))

        return (
            f"Profile evaluated. "
            f"Score: {averaged_score}/100. "
            f"Level: {level}. "
            f"{summary}"
        )

    @gl.public.write
    def submit_review(
        self,
        user_address: str,
        review_url: str,
        context: str,
    ) -> str:
        existing = self._get(user_address, "score")
        assert existing, "Profile not found"
        assert len(review_url) >= 10, "Review URL is too short"

        description = self._get(user_address, "description")
        current_score = int(self._get(user_address, "score") or "0")
        review_count = int(self._get(user_address, "review_count") or "0")

        def leader_fn():
            web_data = ""
            try:
                response = gl.nondet.web.get(review_url)
                raw = response.body.decode("utf-8")
                web_data = raw[:2000]
            except Exception:
                web_data = "Could not fetch review content."

            prompt = f"""You are an AI evaluator updating a developer's reputation score
based on a new review or evidence of their work.

User Description: {description}

Review Context: {context}

Evidence Content from {review_url}:
{web_data}

Based on this new evidence, provide a reputation score update.
Score from 0 to 100 and level from this scale:

0 to 20: newcomer
21 to 40: beginner
41 to 60: intermediate
61 to 80: experienced
81 to 100: expert

Respond ONLY with this JSON:
{{"score": 70, "level": "experienced", "summary": "two sentences describing this review"}}

No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            score = int(data.get("score", 50))
            level = data.get("level", "newcomer")
            summary = data.get("summary", "")

            score = max(0, min(100, score))
            if level not in ("newcomer", "beginner", "intermediate", "experienced", "expert"):
                level = "newcomer"

            return json.dumps({
                "score": score,
                "level": level,
                "summary": summary
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)
                if leader_data["level"] != validator_data["level"]:
                    return False
                return abs(leader_data["score"] - validator_data["score"]) <= 10
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        new_score = data["score"]
        level = data["level"]
        summary = data["summary"]

        averaged_score = (current_score + new_score) // 2
        new_review_count = review_count + 1

        self._set(user_address, "score", str(averaged_score))
        self._set(user_address, "level", level)
        self._set(user_address, "summary", summary)
        self._set(user_address, "review_count", str(new_review_count))

        return (
            f"Review submitted. "
            f"Updated score: {averaged_score}/100. "
            f"Level: {level}. "
            f"{summary}"
        )

    def _get(self, user_address: str, field: str) -> str:
        key = f"{user_address}_{field}:"
        for i in range(len(self.user_data)):
            if self.user_data[i].startswith(key):
                return self.user_data[i][len(key):]
        return ""

    def _set(self, user_address: str, field: str, value: str) -> None:
        key = f"{user_address}_{field}:"
        for i in range(len(self.user_data)):
            if self.user_data[i].startswith(key):
                self.user_data[i] = f"{key}{value}"
                return
        self.user_data.append(f"{key}{value}")

            
        l
