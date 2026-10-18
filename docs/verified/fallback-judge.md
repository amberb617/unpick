# Fallback judge (in-process llama-cpp-python): verified claims

One line per claim. UNVERIFIED means we could not confirm it, not that it is false.
No model weights were downloaded. Sizes and sha256 come from the Hugging Face tree API LFS metadata (`/api/models/<repo>/tree/main`); params, architecture and context come from `/api/models/<repo>` and `?expand[]=gguf`.

## Recommendation

- Pick: `ibm-granite/granite-4.1-3b` via `ibm-granite/granite-4.1-3b-GGUF` file `granite-4.1-3b-Q4_K_M.gguf`. It meets every requirement: Apache-2.0, 3.40B, non-reasoning instruct, GGUF published by IBM, 2.10 GB, released April 2026. Its chat template has no `<think>` block, so the JSON grammar does not have to fight a reasoning preamble.
- Alternate 1: `Qwen/Qwen3-4B-Instruct-2507` via `unsloth/Qwen3-4B-Instruct-2507-GGUF`. It has the highest IFEval score of the group, but 4.02B params is just over the 4B cap, and Qwen publishes no GGUF of it.
- Alternate 2: `mistralai/Ministral-3-3B-Instruct-2512` via `mistralai/Ministral-3-3B-Instruct-2512-GGUF`. Apache-2.0, GGUF from Mistral itself, but Mistral publishes no IFEval number for it.

## Pick: IBM Granite 4.1 3B

- Repo `ibm-granite/granite-4.1-3b` at commit `c0650403e44e78ec0262dab1c90914c65b196c4e` (lastModified 2026-05-04) — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b
- License apache-2.0 (card metadata). The repo has no LICENSE file; the card links https://www.apache.org/licenses/LICENSE-2.0 — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 README.md and the tree listing
- 3,402,836,480 params (safetensors total; GGUF metadata agrees) — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b and https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF?expand[]=gguf
- "3B parameter long-context instruct model", release date April 29th, 2026 — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 README.md
- IFEval Avg 82.30 for 3B (8B 87.06, 30B 89.65) — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 README.md
- Context length 131072 (config `max_position_embeddings` and GGUF `context_length`) — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 config.json and the GGUF metadata API
- The GGUF chat template has no `think` / `enable_thinking` handling — verified 2026-10-18 against the `gguf.chat_template` field of https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF?expand[]=gguf
- GGUF architecture `granite` — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF?expand[]=gguf
- GGUF repo `ibm-granite/granite-4.1-3b-GGUF` at commit `ab4701481089b58a082ef63cc1cee738887293ff` (lastModified 2026-04-20) — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF
- `granite-4.1-3b-Q4_K_M.gguf`: 2,099,501,664 bytes, sha256 `662b0626cd58f443baea23559b469df6576a81d349649c59413b36a9fb32eb29` — verified 2026-10-18 against ibm-granite/granite-4.1-3b-GGUF@ab47014810 tree LFS metadata
- `granite-4.1-3b-Q4_0.gguf`: 1,984,608,864 bytes, sha256 `d7e739eb4572c43d20dd6536c12fa29e1fc81b8f48e64048265d558e0441cb0e` — verified 2026-10-18 against ibm-granite/granite-4.1-3b-GGUF@ab47014810 tree LFS metadata
- Pin download URL form: `https://huggingface.co/ibm-granite/granite-4.1-3b-GGUF/resolve/ab4701481089b58a082ef63cc1cee738887293ff/granite-4.1-3b-Q4_K_M.gguf` — UNVERIFIED (URL pattern only; not fetched, because no weights were to be downloaded)
- Runs end to end in llama-cpp-python 0.3.36 with `response_format` JSON schema — UNVERIFIED (not executed; no weights downloaded)

## Alternate 1: Qwen3-4B-Instruct-2507

- Repo `Qwen/Qwen3-4B-Instruct-2507` at commit `cdbee75f17c01a7cc42f958dc650907174af0554` (lastModified 2025-09-17) — verified 2026-10-18 against https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507
- License apache-2.0, LICENSE file https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE (HTTP 200, "Apache License Version 2.0, January 2004") — verified 2026-10-18 against Qwen/Qwen3-4B-Instruct-2507@cdbee75f17
- 4,022,468,096 params. That is 0.6% over a strict 4.0B cap — verified 2026-10-18 against https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507
- IFEval 83.4 (Qwen3-4B non-thinking 81.2) — verified 2026-10-18 against Qwen/Qwen3-4B-Instruct-2507@cdbee75f17 README.md
- Context 262144 — verified 2026-10-18 against Qwen/Qwen3-4B-Instruct-2507@cdbee75f17 config.json
- `Qwen/Qwen3-4B-Instruct-2507-GGUF` and `ggml-org/Qwen3-4B-Instruct-2507-GGUF` do not exist (API returns 401) — verified 2026-10-18 against https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507-GGUF
- GGUF repo `unsloth/Qwen3-4B-Instruct-2507-GGUF` at commit `a06e946bb6b655725eafa393f4a9745d460374c9` — verified 2026-10-18 against https://huggingface.co/api/models/unsloth/Qwen3-4B-Instruct-2507-GGUF
- `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`: 2,497,281,120 bytes, sha256 `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` — verified 2026-10-18 against unsloth/Qwen3-4B-Instruct-2507-GGUF@a06e946bb6 tree LFS metadata
- Second source: `lmstudio-community/Qwen3-4B-Instruct-2507-GGUF@4edb920b6f14e3b9284d4502a6485103d72cde05`, `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, 2,497,280,448 bytes, sha256 `8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc` — verified 2026-10-18 against its tree LFS metadata

## Alternate 2: Ministral 3 3B Instruct 2512

- Repo `mistralai/Ministral-3-3B-Instruct-2512` at commit `b35d4dfe56c142746f54dbd64f579faab2744308` (lastModified 2026-07-15) — verified 2026-10-18 against https://huggingface.co/api/models/mistralai/Ministral-3-3B-Instruct-2512
- License apache-2.0 (card metadata). There is no LICENSE file in either the model repo or the GGUF repo; the canonical text is https://www.apache.org/licenses/LICENSE-2.0 — verified 2026-10-18 against the tree listings
- 3,849,090,048 params total: a 3.4B language model plus a 0.4B vision encoder. The GGUF holds 3,429,006,336 params (text only) — verified 2026-10-18 against the model API, README.md, and the GGUF metadata API
- Card recommends temperature below 0.1 for production — verified 2026-10-18 against mistralai/Ministral-3-3B-Instruct-2512@b35d4dfe56 README.md
- Context 262144; GGUF arch `mistral3` — verified 2026-10-18 against https://huggingface.co/api/models/mistralai/Ministral-3-3B-Instruct-2512-GGUF?expand[]=gguf
- GGUF repo `mistralai/Ministral-3-3B-Instruct-2512-GGUF` at commit `eb599d408350ea2bb60452cb86be7c7b2fc28227` — verified 2026-10-18 against https://huggingface.co/api/models/mistralai/Ministral-3-3B-Instruct-2512-GGUF
- `Ministral-3-3B-Instruct-2512-Q4_K_M.gguf`: 2,147,023,008 bytes, sha256 `9ed150d4367e68df0ac8e1540f6ddc65b42d0ee26378329d1ecbca60f93fc5f8` — verified 2026-10-18 against mistralai/Ministral-3-3B-Instruct-2512-GGUF@eb599d4083 tree LFS metadata
- IFEval or JSON benchmark published for Ministral 3 3B — UNVERIFIED (none in the model card)

## Other candidates checked

- `ibm-granite/granite-4.2-3b@e459acceac81e5fe67c07d9cfc72329a332e7eb1`: Apache-2.0, 3,659,737,600 params, released 2026-08-25. It is a reasoning model whose thinking mode is the default; the template appends `<think>\n` unless `enable_thinking=False` — verified 2026-10-18 against its README.md. GGUF `ibm-granite/granite-4.2-3b-GGUF@c40945d71cd90f249a56985e8155551a9188dc30` `granite-4.2-3b-Q4_K_M.gguf` is 2,244,011,552 bytes, sha256 `e0406663965846ae22a403456eb826ccce5f450840491f71952f18a7cb78e7d5` — verified 2026-10-18 against its tree LFS metadata. Not picked: the default thinking prefix conflicts with a JSON-only grammar.
- `microsoft/Phi-4-mini-instruct@cfbefacb99257ffa30c83adab238a50856ac3083`: MIT (https://huggingface.co/microsoft/Phi-4-mini-instruct/resolve/main/LICENSE), 3,836,021,760 params, context 131072. `bartowski/microsoft_Phi-4-mini-instruct-GGUF@7ff82c2aaa4dde30121698a973765f39be5288c0` `microsoft_Phi-4-mini-instruct-Q4_K_M.gguf` is 2,491,874,688 bytes, sha256 `01999f17c39cc3074afae5e9c539bc82d45f2dd7faa3917c66cbef76fce8c0c2` — verified 2026-10-18 against the HF API and tree LFS metadata. Qualifies, but the GGUF is from February 2025.
- `HuggingFaceTB/SmolLM3-3B@a07cc9a04f16550a088caea529712d1d335b0ac1`: Apache-2.0, 3,075,098,624 params, context 65536, extended thinking on by default (`/no_think` turns it off). `ggml-org/SmolLM3-3B-GGUF@4965cb60b150737b68a0408c36aeefb65078f894` `SmolLM3-Q4_K_M.gguf` is 1,915,305,312 bytes, sha256 `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e` — verified 2026-10-18 against the HF API, README.md and tree LFS metadata
- `Qwen/Qwen3.5-2B@15852e8c16360a2fea060d615a32b45270f8a8fc`: Apache-2.0, 2,274,069,824 params, pipeline `image-text-to-text`. `Qwen/Qwen3.5-4B` has 4,659,865,088 params (over the cap) — verified 2026-10-18 against the HF API. Not evaluated further.
- `google/gemma-4-E4B-it` has 7,996,156,490 params and `gemma-4-E2B-it` has 5,123,178,051, both over the cap. Card metadata says `license: apache-2.0` with `license_link` https://ai.google.dev/gemma/docs/gemma_4_license — verified 2026-10-18 against the HF API. Whether that page grants plain Apache-2.0 is UNVERIFIED (the page text did not resolve the question); moot, since both exceed 4B.
- LiquidAI LFM2.5 small models — license not checked; UNVERIFIED.

## llama-cpp-python

- Latest is 0.3.36, uploaded 2026-10-01; PyPI has only an sdist (no wheels) for 0.3.25 through 0.3.36 — verified 2026-10-18 against https://pypi.org/pypi/llama-cpp-python/json
- The README lists a C compiler as a requirement (Windows: Visual Studio or MinGW; macOS: Xcode) and says `pip install llama-cpp-python` builds llama.cpp from source — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 README.md
- Prebuilt CPU wheels for 0.3.36 are on `--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`: `win_amd64`, `manylinux2014_x86_64`, `manylinux2014_aarch64`, `musllinux_1_2_{x86_64,aarch64}`, `macosx_11_0_arm64`, `linux_riscv64`, all tagged `py3-none` (one wheel per platform covers any Python 3.8+) — verified 2026-10-18 against https://abetlen.github.io/llama-cpp-python/whl/cpu/llama-cpp-python/
- No wheel exists for macOS x86_64 (the last was 0.3.2) or Windows arm64; those platforms compile from source — verified 2026-10-18 against the same index
- 0.3.36 release asset digests: win_amd64 7,767,370 bytes `sha256:ae5e88a2cf464e5a2dde7c8898c2d5c71cc24d03cac6396bf7509456bde0b9fb`; manylinux x86_64 `sha256:c8a3e98093e950d7a770f794842e36f2db82b2933e8762ed7b5ffd435011e8e4`; manylinux aarch64 `sha256:410bdf3cf66478f55de0ad51dd6ab241424591bdd36aff086b000d155ac182c6`; macosx arm64 `sha256:1bec5e1d9fc7c4919aaece647bbd3e1a7f36ac8fd2714c8cda7e6991a544557b` — verified 2026-10-18 against GitHub release abetlen/llama-cpp-python v0.3.36 (tag commit 1652066e0a)
- Add `--only-binary=llama-cpp-python` so pip never falls back to the PyPI sdist and compiles — UNVERIFIED (standard pip flag; not tested against this index)
- v0.3.36 vendors llama.cpp commit `0c1e57098bba43ac29e6e3b677cdceebdd22334f` (2026-10-01), between llama.cpp v0.5.0 and v0.6.0 — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 vendor/ and the ggml-org/llama.cpp compare API
- `create_chat_completion(..., temperature=0.2 default, response_format=..., grammar=..., seed=...)` — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama.py:2011-2030
- `response_format` type is `Literal["text","json_object"]` plus an optional `schema`; there is no `"json_schema"` type — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama_types.py:176-180
- `{"type":"json_object","schema":S}` becomes `LlamaGrammar.from_json_schema(json.dumps(S))`. If schema conversion raises, it silently falls back to generic JSON (`fallback_to_json=True`), so validate the output against the schema afterwards anyway — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama_chat_format.py:1005-1028
- Explicit alternative: `grammar=LlamaGrammar.from_json_schema(json.dumps(S))` passed to `create_chat_completion` — verified 2026-10-18 against the same files (signature at llama.py:2030; constructor used at llama_chat_format.py:1009)
- `temperature=0.0` selects the greedy sampler (`sampler.add_greedy()`); a negative value selects `add_dist(seed)` — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama.py:761-764
- With no `chat_format`, the GGUF's `tokenizer.chat_template` is used via `Jinja2ChatFormatter`, which renders in `jinja2.sandbox.ImmutableSandboxedEnvironment` — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama.py:512-560 and llama_chat_format.py:27,221

## CVEs (2024-2026) and the minimum safe version

- CVE-2024-34359 (GHSA-56xg-wfcc-g829, critical): RCE through Jinja2 SSTI in the GGUF chat template, affecting llama-cpp-python 0.2.30 through 0.2.71, fixed in 0.2.72 — verified 2026-10-18 against the GitHub Advisory DB (`gh api advisories?ecosystem=pip&affects=llama-cpp-python`)
- GGUF-parser and model-load advisories in llama.cpp, with the patched build: CVE-2024-32878 b2740; CVE-2024-41130 b3427; CVE-2024-42477 b3561; CVE-2025-49847 b5662 (vocab); CVE-2025-52566 b5721 (tokenizer); GHSA-g4cc-763q-h9h6 c33fe8b8 (llama_model_load); CVE-2025-53630 26a48ad (gguf integer overflow); CVE-2026-33298 b7824 (`ggml_nbytes` overflow, heap overflow); CVE-2026-27940 b8146 (bypass of the 53630 fix, demonstrated to RCE) — verified 2026-10-18 against `gh api repos/ggml-org/llama.cpp/security-advisories` and NVD
- CVE-2026-52131: reachable assertion in `gguf_reader::read`, affects b5693 and earlier — verified 2026-10-18 against NVD keywordSearch=llama.cpp
- b7824 = 4e5b83b226 (2026-01-24); b8146 = 418dea39ce (2026-02-24) — verified 2026-10-18 against the ggml-org/llama.cpp commits API
- llama-cpp-python 0.3.16 (2025-08-15) vendors a llama.cpp older than b8146; 0.3.17 (2026-03-23) is the first release whose vendored commit (49bfddeca1) contains b8146 — verified 2026-10-18 against abetlen/llama-cpp-python vendor/ at each tag and the compare API
- **Minimum safe for GGUF parsing: llama-cpp-python 0.3.17. Pin 0.3.36**, the latest release and the first with wheels on every target platform except Intel Mac and Windows arm64 — derived from the lines above
- CVE-2026-43627 (`llama_batch_init` integer overflow, "b1283 through b9058"). Only reachable with attacker-chosen batch parameters, which a fixed-config judge does not have. Whether upstream has a fix is UNVERIFIED (NVD cites only third-party patches; tag b9059 does not exist) — verified 2026-10-18 against NVD
- CVE-2026-2069 (stack overflow in `llama_grammar_advance_stack`): fix PR #18993 is unmerged and issue #18988 is open. Only reachable with an attacker-controlled grammar; the judge's schema is ours, not the input file's — verified 2026-10-18 against ggml-org/llama.cpp issues/18988 and pulls/18993
- CVE-2026-17500/17501 (`common/json-schema-to-grammar.cpp`), CVE-2026-18581 (`common/jinja/parser.cpp`) and CVE-2026-107183 (llama-server chat-peg, fixed b11393 = dbe4c3ed42, 2026-10-04, newer than 0.3.36's vendored commit) are in llama.cpp's `common/` or server code. llama-cpp-python converts schemas in Python (`llama_grammar.py`) and renders templates in Python Jinja2. Whether the 0.3.36 wheel links any of that `common/` code is UNVERIFIED — verified 2026-10-18 against NVD and abetlen/llama-cpp-python@v0.3.36 source
- RPC and server CVEs (CVE-2024-42479, CVE-2026-34159, CVE-2026-21869, CVE-2026-43631/43632, CVE-2026-78147/78148, CVE-2026-86317) do not apply to in-process CPU use — verified 2026-10-18 against the advisory and NVD descriptions (each names the RPC backend or llama-server)

## Pure-wheel alternative: onnxruntime-genai

- onnxruntime-genai 0.18.0 (2026-10-14, MIT) ships wheels for cp311-cp314 on win_amd64, win_arm64, manylinux_2_28 x86_64 and aarch64, and macosx_12_0_arm64. There are no cp310 or macOS x86_64 wheels — verified 2026-10-18 against https://pypi.org/pypi/onnxruntime-genai/json
- The latest GitHub release/tag is v0.17.0, although PyPI has 0.18.0 — verified 2026-10-18 against `gh api repos/microsoft/onnxruntime-genai/releases`
- Constrained decoding goes through `params.set_guidance(guidance_type, guidance_data)` with type `"json_schema"` (or `"lark_grammar"`) — verified 2026-10-18 against microsoft/onnxruntime-genai@v0.17.0 examples/python/model-qa.py:92 and common.py:565-580
- No qualifying model at 3 GB or less: `microsoft/Phi-4-mini-instruct-onnx@fc04c8f93d` CPU int4 `model.onnx.data` is 4,856,573,952 bytes; `onnx-community/Qwen3-4B-Instruct-2507-ONNX` is a multi-shard fp32/fp16 transformers.js export (each shard about 2 GB); `onnx-community/granite-4.1-3b-ONNX` does not exist — verified 2026-10-18 against the HF tree API. A user would have to build an int4 ONNX themselves, so this route is not viable for a one-file pinned download.
