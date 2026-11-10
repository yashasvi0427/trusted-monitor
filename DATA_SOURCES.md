# Data attribution and scope

The 100 task subset and reference/test code in `data/problems.json` come from the sanitized MBPP dataset, Google Research / Austin et al., *Program Synthesis with Large Language Models* (2021), https://arxiv.org/abs/2108.07732. Official dataset: https://huggingface.co/datasets/google-research-datasets/mbpp, licensed CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. We selected a fixed-seed subset, added evaluation/cache metadata and retained task IDs; original problem statements and reference code are attributed to their authors.

Model replies and prompts are personal-project artifacts generated with Qwen2.5-Coder 7B and 1.5B through Ollama. They include deliberately incorrect toy puzzle solutions for evaluation, not real-world exploit code. No model weights are redistributed. Reference disagreement is not proof of malicious intent. The validator subprocess is not a hardened sandbox; review code before execution.

This project is a small AI-assisted replication of trusted monitoring from *AI Control: Improving Safety Despite Intentional Subversion* (Greenblatt et al., 2023), https://arxiv.org/abs/2312.06942. No novel research mechanism or general monitoring effectiveness is established.
