# GenLayer Reputation System

An onchain reputation system where AI validators evaluate developer profiles and assign scores based on publicly verifiable evidence. Built on GenLayer Testnet Bradbury.

---

## What is this

One of the hardest problems in decentralized work is trusting someone you have never worked with. Most platforms solve this with centralized ratings that can be manipulated or deleted. I built this to explore whether AI validators on GenLayer could evaluate public evidence like GitHub profiles and assign reputation scores that live onchain and cannot be altered by any single party.

The score is not based on someone's word. It is based on what the AI can actually verify from public URLs, and multiple validators have to agree on the result before anything is committed to the chain.

---

## How it works

A developer registers their profile with a GitHub URL and a short description. Anyone can then trigger an evaluation where the AI fetches the GitHub profile, reads the content, and assigns a score from 0 to 100 along with a level. Additional reviews can be submitted with new evidence URLs that update the score as a running average. The more evidence submitted, the more accurate the reputation becomes over time.

The five levels are newcomer for scores 0 to 20, beginner for 21 to 40, intermediate for 41 to 60, experienced for 61 to 80, and expert for 81 to 100.

---

## Functions

register takes a GitHub URL and a short description and creates the profile onchain.

evaluate_profile takes a user address and triggers the AI evaluation. The contract fetches the GitHub URL and assigns a score and level through Optimistic Democracy consensus.

submit_review takes a user address, an evidence URL, and context about the work. The AI evaluates the new evidence and updates the score as an average of all previous evaluations.

get_profile shows the full profile including score, level, number of reviews, and the latest summary.

---

## Test results

Registered a profile pointing to the genlayerlabs GitHub organization. The initial evaluation returned a score of 15 and level newcomer because the fetched content did not show enough verifiable activity. After submitting a review with the GenLayer Studio repository as evidence and context about active contributions on Testnet Bradbury, the score updated to 42 and the level moved to experienced. The summary accurately reflected the new evidence.

---

## How to run it

Go to GenLayer Studio at https://studio.genlayer.com and create a new file called reputation_system.py. Paste the contract code and set execution mode to Normal Full Consensus. Deploy with your address as owner_address.

Follow this order and wait for FINALIZED at each step. Run get_summary first, then register with your GitHub URL and description, then evaluate_profile with your address, then get_profile to see the initial score. You can then run submit_review with additional evidence and get_profile again to see the updated score.

Note: the contract in this repository uses the Address type in the constructor as required by genvm-lint. When deploying in GenLayer Studio use a version that receives str in the constructor and converts internally with Address(owner_address) since Studio requires primitive types to parse the contract schema correctly.

---

## Resources

GenLayer Docs: https://docs.genlayer.com

Optimistic Democracy: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy

Equivalence Principle: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/equivalence-principle

GenLayer Studio: https://studio.genlayer.com

Discord: https://discord.gg/8Jm4v89VAu
